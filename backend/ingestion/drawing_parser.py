"""
drawing_parser.py — P&ID / Engineering Drawing Parser
Three-tier approach:
  1. PRIMARY:   PaddleOCR (Python 3.10 subprocess via venv_paddle/) — best for scanned drawings
  2. SECONDARY: Hugging Face Vision Model (via Inference API) — great for complex P&ID diagrams
  3. FALLBACK:  PyMuPDF text extraction + regex equipment tag detection

To enable PaddleOCR, run: bash scripts/setup_paddleocr.sh
"""
import os
import re
import base64
import json
import tempfile
import fitz  # PyMuPDF
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


try:
    from huggingface_hub import InferenceClient
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    if HF_TOKEN:
        VISION_MODEL_ID = os.getenv(
            "HF_VISION_MODEL",
            "Qwen/Qwen2.5-VL-7B-Instruct"  # Best overall for P&ID understanding
        )
        client = InferenceClient(
            model=VISION_MODEL_ID,
            token=HF_TOKEN,
            timeout=60
        )
        logger.info(f"✅ Hugging Face Inference client initialized with {VISION_MODEL_ID}")
    else:
        client = None
        logger.warning("⚠️ HF_TOKEN not set. Vision model unavailable.")
        
except ImportError:
    logger.warning("⚠️ huggingface_hub not installed. Vision model unavailable.")
    client = None
try:
    from .paddle_wrapper import run_paddle_ocr, is_paddle_available, extract_text_from_image as _paddle_extract
except ImportError:
    try:
        from backend.ingestion.paddle_wrapper import run_paddle_ocr, is_paddle_available, extract_text_from_image as _paddle_extract
    except ImportError:
        def is_paddle_available(): return False  # type: ignore
        def run_paddle_ocr(*a, **kw): return None  # type: ignore
        def _paddle_extract(*a, **kw): return ""  # type: ignore

# Equipment tag pattern: P-201, VLV-101, C-101, T-301, E-401, etc.
EQUIPMENT_TAG_PATTERN = re.compile(r'\b([A-Z]{1,4}-\d{2,4}[A-Z]?)\b')

# Type mapping for equipment tags
TYPE_MAP = {
    'P': 'Pump', 'C': 'Compressor', 'T': 'Tank/Tower', 'E': 'Heat Exchanger',
    'V': 'Valve', 'VLV': 'Valve', 'FCV': 'Flow Control Valve', 'LCV': 'Level Control Valve',
    'PCV': 'Pressure Control Valve', 'TCV': 'Temperature Control Valve',
    'PSV': 'Pressure Safety Valve', 'FI': 'Flow Indicator', 'PI': 'Pressure Indicator',
    'TI': 'Temperature Indicator', 'LI': 'Level Indicator', 'XI': 'Vibration Indicator',
    'FIC': 'Flow Indicator Controller', 'PIC': 'Pressure Indicator Controller',
    'TIC': 'Temperature Indicator Controller', 'LIC': 'Level Indicator Controller',
    'MCC': 'Motor Control Centre', 'XS': 'Vibration Switch', 'TS': 'Temperature Switch'
}

# Image extensions for raw image handling
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}

# ============================================================
# Helper Functions
# ============================================================

def _extract_tags_with_regex(text: str) -> List[Dict]:
    """Regex-based equipment tag extraction from text."""
    tags = []
    seen = set()
    
    if not text:
        return tags
    
    for match in EQUIPMENT_TAG_PATTERN.finditer(text):
        tag = match.group(1)
        if tag in seen:
            continue
        seen.add(tag)
        
        # Infer type from prefix
        prefix_match = re.match(r'^([A-Z]+)', tag)
        prefix = prefix_match.group(1) if prefix_match else ''
        eq_type = TYPE_MAP.get(prefix, 'Equipment')
        
        tags.append({
            "tag": tag,
            "type": eq_type,
            "description": f"{eq_type} {tag}",
            "source": "regex"
        })
    return tags


def _extract_json_from_response(text: str) -> Optional[Dict]:
    """
    Robust JSON extraction from model response.
    Handles code fences, explanatory text, and malformed JSON.
    """
    if not text:
        return None
    
    # Remove markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text.strip(), flags=re.MULTILINE)
    
    # Try to find JSON object in the text
    # First, try to find anything between { and }
    json_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', re.DOTALL)
    matches = json_pattern.findall(text)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            return parsed
        except json.JSONDecodeError:
            continue
    
    # If no JSON object found, try to parse the whole text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    logger.warning("⚠️ Could not extract valid JSON from model response")
    return None


def _call_hf_vision(image_bytes: bytes, mime_type: str = "image/png") -> Optional[Dict]:
    """
    Send an image to Hugging Face Vision model and get equipment tag annotations.
    Uses the InferenceClient's image-to-text or chat completion API.
    Returns parsed JSON dict or None if unavailable.
    """
    if not client or not HF_TOKEN:
        logger.warning("⚠️ HF Vision client not available")
        return None

    try:
        # Encode image as base64
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{b64_image}"
        
        # Build prompt for P&ID analysis
        prompt = (
            "You are an expert P&ID (Piping and Instrumentation Diagram) interpreter "
            "for a petroleum refinery. Analyze this engineering drawing and extract ALL "
            "equipment tags, instrument tags, and valve tags visible.\n\n"
            "Return ONLY a valid JSON object with this structure:\n"
            "{\n"
            "  \"equipment_tags\": [\n"
            "    {\"tag\": \"P-201\", \"type\": \"Pump\", \"description\": \"Crude Oil Transfer Pump\"},\n"
            "    {\"tag\": \"V-201A\", \"type\": \"Valve\", \"description\": \"Suction Isolation Valve\"}\n"
            "  ],\n"
            "  \"connections\": [\n"
            "    {\"from\": \"P-201\", \"to\": \"V-201B\", \"line\": \"Process line 6\\\"\"}\n"
            "  ],\n"
            "  \"drawing_type\": \"P&ID\",\n"
            "  \"unit\": \"Crude Distillation Unit\"\n"
            "}\n\n"
            "If you cannot read equipment tags clearly, make your best inference from "
            "standard refinery P&ID conventions. Return ONLY the JSON, no other text."
        )
        
        # Try different API approaches based on what's available
        
        # Approach 1: Chat completion (works with some HF endpoints)
        try:
            response = client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_data_url}}
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            if response and response.choices:
                result_text = response.choices[0].message.content
                parsed = _extract_json_from_response(result_text)
                if parsed:
                    logger.info("✅ HF Vision model successfully processed image (chat_completion)")
                    return parsed
        except Exception as e:
            logger.debug(f"Chat completion API not supported: {e}")
        
        # Approach 2: Image-to-text (fallback for standard HF Inference API)
        try:
            # Some HF endpoints support direct image-to-text
            response = client.image_to_text(
                image=image_bytes,
                prompt=prompt
            )
            
            if response:
                result_text = response.generated_text if hasattr(response, 'generated_text') else str(response)
                parsed = _extract_json_from_response(result_text)
                if parsed:
                    logger.info("✅ HF Vision model successfully processed image (image_to_text)")
                    return parsed
        except Exception as e:
            logger.debug(f"Image-to-text API not supported: {e}")
        
        # Approach 3: Custom inference with raw API (most compatible)
        try:
            import requests
            
            # Use the inference API endpoint directly
            api_url = f"https://api-inference.huggingface.co/models/{VISION_MODEL_ID}"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            # Prepare the payload
            payload = {
                "inputs": {
                    "image": image_data_url,
                    "text": prompt
                },
                "parameters": {
                    "temperature": 0.1,
                    "max_new_tokens": 2048
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    result_text = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    result_text = result.get('generated_text', '')
                else:
                    result_text = str(result)
                
                parsed = _extract_json_from_response(result_text)
                if parsed:
                    logger.info("✅ HF Vision model successfully processed image (raw inference)")
                    return parsed
            else:
                logger.warning(f"⚠️ HF API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.debug(f"Raw inference API not supported: {e}")
        
        logger.warning("⚠️ All HF Vision API approaches failed")
        return None
            
    except Exception as e:
        logger.error(f"❌ HF Vision call failed: {e}")
        return None


def _parse_raw_image(file_path: str, results: dict) -> dict:
    """
    Handle raw image files (PNG/JPG etc.) directly.
    Routes: HF Vision → PaddleOCR → regex on empty string fallback.
    """
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "image/png"

    with open(file_path, "rb") as f:
        img_bytes = f.read()

    results['metadata'] = {
        'title': os.path.basename(file_path),
        'page_count': 1,
        'source_file': file_path,
        'file_type': 'image'
    }

    # ── Tier 1: PaddleOCR ──────────────────────────────────────
    if is_paddle_available():
        try:
            paddle_results = run_paddle_ocr(file_path, timeout=45)
            if paddle_results:
                combined_text = " ".join(r["text"] for r in paddle_results if r.get("text"))
                tags = _extract_tags_with_regex(combined_text)
                results['equipment_tags'] = tags
                results['full_text'] = combined_text
                results['pages'] = [{'page': 1, 'text': combined_text, 'tags_found': len(tags), 'parse_method': 'paddleocr'}]
                results['parse_method'] = 'paddleocr'
                results['success'] = True
                logger.info(f"✅ Drawing parser (image/paddleocr): {len(tags)} tags from {os.path.basename(file_path)}")
                return results
        except Exception as e:
            logger.error(f"❌ PaddleOCR error on image: {e}")

    # ── Tier 2: HF Vision ──────────────────────────────────────
    if client and HF_TOKEN:
        try:
            parsed = _call_hf_vision(img_bytes, mime_type)
            if parsed:
                page_tags = parsed.get("equipment_tags", [])
                page_connections = parsed.get("connections", [])
                for t in page_tags:
                    t["page"] = 1
                    t["source"] = "hf_vision"
                results['equipment_tags'] = page_tags
                results['connections'] = page_connections
                results['drawing_type'] = parsed.get("drawing_type", "Engineering Drawing")
                results['pages'] = [{'page': 1, 'tags_found': len(page_tags), 'parse_method': 'hf_vision'}]
                results['parse_method'] = 'hf_vision'
                results['full_text'] = f"[HF Vision extracted {len(page_tags)} equipment tags]"
                results['success'] = True
                logger.info(f"✅ Drawing parser (image/hf_vision): {len(page_tags)} tags from {os.path.basename(file_path)}")
                return results
        except Exception as e:
            logger.error(f"❌ HF Vision failed on image {os.path.basename(file_path)}: {e}")

    # ── Tier 3: Fallback ──────────────────────────────────────
    results['pages'] = [{'page': 1, 'text': '', 'tags_found': 0, 'parse_method': 'image_fallback'}]
    results['parse_method'] = 'image_fallback'
    results['full_text'] = ''
    results['equipment_tags'] = []
    results['success'] = True
    logger.warning(f"⚠️ Drawing parser (image/fallback): No OCR available, returning empty for {os.path.basename(file_path)}")

    return results


def parse_drawing(file_path: str) -> Dict:
    """
    Main entry point. Parses P&ID / engineering drawings and raw images.
    Priority: PaddleOCR → HF Vision → PyMuPDF+regex.
    
    Returns:
        {
            'pages': [...],
            'metadata': {...},
            'parse_method': 'paddleocr' | 'hf_vision' | 'text_regex' | 'fallback',
            'equipment_tags': [...],
            'connections': [...],
            'drawing_type': str,
            'success': bool
        }
    """
    results = {
        'pages': [],
        'metadata': {},
        'parse_method': 'unknown',
        'equipment_tags': [],
        'connections': [],
        'drawing_type': 'Engineering Drawing',
        'success': False,
        'source_file': file_path
    }

    if not os.path.exists(file_path):
        results['error'] = f"File not found: {file_path}"
        return results

    # ── Route raw image files ─────────────────────────────────
    ext = os.path.splitext(file_path)[1].lower()
    if ext in IMAGE_EXTS:
        return _parse_raw_image(file_path, results)

    # ── Process PDF files ─────────────────────────────────────
    try:
        doc = fitz.open(file_path)
        results['metadata'] = {
            'title': doc.metadata.get('title', os.path.basename(file_path)),
            'page_count': len(doc),
            'source_file': file_path,
            'created_at': datetime.now().isoformat()
        }

        all_tags = []
        all_connections = []
        all_text = []
        parse_method = 'text_regex'

        for page_num, page in enumerate(doc, start=1):
            
            # ── Tier 1: PaddleOCR ──────────────────────────────────────────
            if is_paddle_available():
                try:
                    pix = page.get_pixmap(dpi=200)
                    tmp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp_path = tmp.name
                            pix.save(tmp_path)
                        
                        paddle_results = run_paddle_ocr(tmp_path, timeout=45)
                        if paddle_results:
                            combined_text = " ".join(r["text"] for r in paddle_results if r.get("text"))
                            tags = _extract_tags_with_regex(combined_text)
                            all_tags.extend(tags)
                            all_text.append(combined_text)
                            parse_method = "paddleocr"
                            all_connections.append({"type": "flow", "source": "paddleocr", "page": page_num})
                            results['pages'].append({
                                'page': page_num,
                                'tags_found': len(tags),
                                'parse_method': 'paddleocr',
                                'text': combined_text
                            })
                            continue  # Skip other methods for this page
                    finally:
                        # Ensure temporary file is cleaned up
                        if tmp_path and os.path.exists(tmp_path):
                            try:
                                os.unlink(tmp_path)
                            except OSError:
                                pass
                except Exception as paddle_err:
                    logger.error(f"❌ PaddleOCR error on page {page_num}: {paddle_err}")

            # ── Tier 2: HF Vision ──────────────────────────────────────────
            if client and HF_TOKEN:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")

                    # Only call Vision if page is likely an image/drawing (few text chars)
                    text_len = len(page.get_text().strip())
                    is_drawing = text_len < 200  # Image-heavy page

                    if is_drawing:
                        parsed = _call_hf_vision(img_bytes, "image/png")
                        if parsed:
                            page_tags = parsed.get("equipment_tags", [])
                            page_connections = parsed.get("connections", [])
                            for t in page_tags:
                                t["page"] = page_num
                                t["source"] = "hf_vision"
                            all_tags.extend(page_tags)
                            all_connections.extend(page_connections)
                            parse_method = 'hf_vision'
                            results['pages'].append({
                                'page': page_num,
                                'tags_found': len(page_tags),
                                'parse_method': 'hf_vision'
                            })
                            continue
                except Exception as e:
                    logger.error(f"❌ HF Vision failed on page {page_num}: {e}")

            # ── Tier 3: Fallback: Text extraction + regex ────────────────
            page_text = page.get_text()
            all_text.append(page_text)
            page_tags = _extract_tags_with_regex(page_text)
            for t in page_tags:
                t["page"] = page_num
            all_tags.extend(page_tags)
            results['pages'].append({
                'page': page_num,
                'text': page_text,
                'tags_found': len(page_tags),
                'parse_method': 'text_regex'
            })

        # De-duplicate tags (keep first occurrence per tag ID)
        seen = set()
        unique_tags = []
        for t in all_tags:
            tag_id = t.get('tag', '')
            if tag_id and tag_id not in seen:
                seen.add(tag_id)
                unique_tags.append(t)

        results['equipment_tags'] = unique_tags
        results['connections'] = all_connections
        results['parse_method'] = parse_method
        results['full_text'] = "\n".join(all_text)
        results['success'] = True

        logger.info(f"✅ Drawing parser: {len(unique_tags)} tags extracted from {os.path.basename(file_path)} (method: {parse_method})")
        return results

    except Exception as e:
        results['error'] = str(e)
        results['parse_method'] = 'error'
        logger.error(f"❌ Drawing parser error for {file_path}: {e}")
        return results


def get_vision_model_info() -> Dict[str, Any]:
    """Get information about the configured vision model."""
    return {
        'provider': 'Hugging Face',
        'model': VISION_MODEL_ID if HF_TOKEN else 'Not configured',
        'available': bool(client and HF_TOKEN),
        'api_key_set': bool(HF_TOKEN),
        'paddle_available': is_paddle_available()
    }


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Drawing Parser Test")
    print("=" * 60)
    
    # Show configuration
    info = get_vision_model_info()
    print("\n Configuration:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test with a sample file if provided
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"\n Parsing: {test_file}")
        result = parse_drawing(test_file)
        print(f"\n Results:")
        for key, value in result.items():
            if key not in ['pages', 'full_text']:
                print(f"  {key}: {value}")
        print(f"  pages: {len(result.get('pages', []))}")
        print(f"  tags: {result.get('equipment_tags', [])[:5]}...")
    else:
        print("\n💡 Usage: python drawing_parser.py <path_to_drawing>")