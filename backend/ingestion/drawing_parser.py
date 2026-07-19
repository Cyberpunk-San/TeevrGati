"""
drawing_parser.py — P&ID / Engineering Drawing Parser
Three-tier approach:
  1. PRIMARY:   PaddleOCR (Python 3.10 subprocess via venv_paddle/) — best for scanned drawings
  2. SECONDARY: Gemini Vision API — great for complex P&ID diagrams
  3. FALLBACK:  PyMuPDF text extraction + regex equipment tag detection

To enable PaddleOCR, run: bash scripts/setup_paddleocr.sh
"""
import os
import re
import base64
import json
import fitz  # PyMuPDF
from PIL import Image
from typing import Dict, List, Optional

# PaddleOCR subprocess wrapper (Python 3.10 venv) — graceful no-op if not installed
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
EQUIPMENT_TAG_PATTERN = re.compile(
    r'\b([A-Z]{1,4}-\d{2,4}[A-Z]?)\b'
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _call_gemini_vision(image_bytes: bytes, mime_type: str = "image/png") -> Optional[str]:
    """
    Send an image to Gemini Vision API and get equipment tag annotations back as JSON.
    Returns raw JSON string or None if unavailable.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        import urllib.request
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            "You are an expert P&ID (Piping and Instrumentation Diagram) interpreter "
                            "for a petroleum refinery. Analyze this engineering drawing and extract ALL "
                            "equipment tags, instrument tags, and valve tags visible. "
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
                            "}\n"
                            "If you cannot read equipment tags clearly, make your best inference from "
                            "standard refinery P&ID conventions. Return ONLY the JSON, no other text."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image
                        }
                    }
                ]
            }],
            "generationConfig": {"temperature": 0.1}
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            # Strip markdown code fences if present
            text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
            text = re.sub(r'\s*```$', '', text.strip(), flags=re.MULTILINE)
            return text.strip()
    except Exception as e:
        print(f"⚠️ Gemini Vision call failed: {e}")
        return None


def _extract_tags_with_regex(text: str) -> List[Dict]:
    """Regex-based equipment tag extraction from text."""
    tags = []
    seen = set()
    for match in EQUIPMENT_TAG_PATTERN.finditer(text):
        tag = match.group(1)
        if tag in seen:
            continue
        seen.add(tag)
        # Infer type from prefix
        prefix = re.match(r'^([A-Z]+)', tag).group(1)
        type_map = {
            'P': 'Pump', 'C': 'Compressor', 'T': 'Tank/Tower', 'E': 'Heat Exchanger',
            'V': 'Valve', 'VLV': 'Valve', 'FCV': 'Flow Control Valve', 'LCV': 'Level Control Valve',
            'PCV': 'Pressure Control Valve', 'TCV': 'Temperature Control Valve',
            'PSV': 'Pressure Safety Valve', 'FI': 'Flow Indicator', 'PI': 'Pressure Indicator',
            'TI': 'Temperature Indicator', 'LI': 'Level Indicator', 'XI': 'Vibration Indicator',
            'FIC': 'Flow Indicator Controller', 'PIC': 'Pressure Indicator Controller',
            'TIC': 'Temperature Indicator Controller', 'LIC': 'Level Indicator Controller',
            'MCC': 'Motor Control Centre', 'XS': 'Vibration Switch', 'TS': 'Temperature Switch'
        }
        eq_type = type_map.get(prefix, 'Equipment')
        tags.append({
            "tag": tag,
            "type": eq_type,
            "description": f"{eq_type} {tag}",
            "source": "regex"
        })
    return tags


def _parse_raw_image(file_path: str, results: dict) -> dict:
    """
    Handle raw image files (PNG/JPG etc.) directly — no fitz needed.
    Routes: Gemini Vision → PaddleOCR → regex on empty string fallback.
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

    # Tier 1: PaddleOCR
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
                print(f"✅ Drawing parser (image/paddleocr): {len(tags)} tags from {os.path.basename(file_path)}")
                return results
        except Exception as e:
            print(f"[drawing_parser] PaddleOCR error on image: {e}")

    # Tier 2: Gemini Vision
    if GEMINI_API_KEY:
        try:
            gemini_json_str = _call_gemini_vision(img_bytes, mime_type)
            if gemini_json_str:
                parsed = json.loads(gemini_json_str)
                page_tags = parsed.get("equipment_tags", [])
                page_connections = parsed.get("connections", [])
                for t in page_tags:
                    t["page"] = 1
                    t["source"] = "gemini_vision"
                results['equipment_tags'] = page_tags
                results['connections'] = page_connections
                results['drawing_type'] = parsed.get("drawing_type", "Engineering Drawing")
                results['pages'] = [{'page': 1, 'tags_found': len(page_tags), 'parse_method': 'gemini_vision'}]
                results['parse_method'] = 'gemini_vision'
                results['full_text'] = f"[Gemini Vision extracted {len(page_tags)} equipment tags]"
                results['success'] = True
                print(f"✅ Drawing parser (image/gemini_vision): {len(page_tags)} tags from {os.path.basename(file_path)}")
                return results
        except Exception as e:
            print(f"⚠️ Gemini Vision failed on image {os.path.basename(file_path)}: {e}")

    # Tier 3: Fallback — try PaddleOCR text extraction on image bytes
    try:
        from PIL import Image as PILImage
        import io
        img = PILImage.open(io.BytesIO(img_bytes))
        # Convert to text via basic analysis — no text available, return empty with success=True
        results['pages'] = [{'page': 1, 'text': '', 'tags_found': 0, 'parse_method': 'image_fallback'}]
        results['parse_method'] = 'image_fallback'
        results['full_text'] = ''
        results['equipment_tags'] = []
        results['success'] = True
        print(f"⚠️ Drawing parser (image/fallback): No OCR available, returning empty for {os.path.basename(file_path)}")
    except Exception as e:
        results['error'] = str(e)

    return results


def parse_drawing(file_path: str) -> Dict:
    """
    Main entry point. Parses P&ID / engineering drawings and raw images.
    Priority: PaddleOCR (if venv_paddle set up) → Gemini Vision → PyMuPDF+regex.
    
    Returns:
        {
            'pages': [...],
            'metadata': {...},
            'parse_method': 'paddleocr' | 'gemini_vision' | 'text_regex' | 'fallback',
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

    # Route raw image files directly — fitz cannot open them
    ext = os.path.splitext(file_path)[1].lower()
    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
    if ext in IMAGE_EXTS:
        return _parse_raw_image(file_path, results)

    try:
        doc = fitz.open(file_path)
        results['metadata'] = {
            'title': doc.metadata.get('title', os.path.basename(file_path)),
            'page_count': len(doc),
            'source_file': file_path
        }

        all_tags = []
        all_connections = []
        all_text = []
        parse_method = 'text_regex'

        for page_num, page in enumerate(doc):
            # ── Tier 1: PaddleOCR via Python 3.10 subprocess ──────────────────
            if is_paddle_available():
                try:
                    pix = page.get_pixmap(dpi=200)
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        tmp_path = tmp.name
                        pix.save(tmp_path)
                    paddle_results = run_paddle_ocr(tmp_path, timeout=45)
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    if paddle_results:
                        combined_text = " ".join(r["text"] for r in paddle_results if r.get("text"))
                        tags = _extract_equipment_tags(combined_text)
                        all_tags.extend(tags)
                        all_text.append(combined_text)
                        parse_method = "paddleocr"
                        all_connections.append({"type": "flow", "source": "paddleocr", "page": page_num + 1})
                        continue  # Skip other methods for this page
                except Exception as paddle_err:
                    print(f"[drawing_parser] PaddleOCR error on page {page_num}: {paddle_err}")

            # ── Tier 2: Gemini Vision (primary for image-based drawings) ──────
            if GEMINI_API_KEY:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")

                    # Only call Vision if page is likely an image/drawing (few text chars)
                    text_len = len(page.get_text().strip())
                    is_drawing = text_len < 200  # Image-heavy page

                    if is_drawing:
                        gemini_json_str = _call_gemini_vision(img_bytes, "image/png")
                        if gemini_json_str:
                            parsed = json.loads(gemini_json_str)
                            page_tags = parsed.get("equipment_tags", [])
                            page_connections = parsed.get("connections", [])
                            for t in page_tags:
                                t["page"] = page_num + 1
                                t["source"] = "gemini_vision"
                            all_tags.extend(page_tags)
                            all_connections.extend(page_connections)
                            parse_method = 'gemini_vision'
                            results['pages'].append({
                                'page': page_num + 1,
                                'tags_found': len(page_tags),
                                'parse_method': 'gemini_vision'
                            })
                            continue
                except Exception as e:
                    print(f"⚠️ Gemini Vision failed on page {page_num+1}: {e}")

            # ── Fallback: Text extraction + regex ────────────────────────────
            page_text = page.get_text()
            all_text.append(page_text)
            page_tags = _extract_tags_with_regex(page_text)
            for t in page_tags:
                t["page"] = page_num + 1
            all_tags.extend(page_tags)
            results['pages'].append({
                'page': page_num + 1,
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

        print(f"✅ Drawing parser: {len(unique_tags)} tags extracted from {os.path.basename(file_path)} (method: {parse_method})")
        return results

    except Exception as e:
        results['error'] = str(e)
        results['parse_method'] = 'error'
        print(f"❌ Drawing parser error for {file_path}: {e}")
        return results
