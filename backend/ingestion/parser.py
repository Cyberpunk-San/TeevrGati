import os
import json
from datetime import datetime
from backend.ingestion import clean_text, scanned_ocr, layout_parser, drawing_parser
from backend.utils.file_utils import detect_file_type, is_drawing

class DocumentParser:
    """
    Main ingestion router with fallback chain.
    """
    def __init__(self):
        self.parsed_docs = []
        self.errors = []
    
    def parse(self, file_path, doc_name=None):
        """
        Main entry point.
        Returns: {
            'success': bool,
            'document_id': str,
            'pages': list,
            'metadata': dict,
            'parse_chain': list,  # What was attempted
            'error': str or None,
            'fallback_used': bool
        }
        """
        print(f"[INFO] Starting parse for: {file_path}")
        
        # Track what we tried
        parse_chain = []
        result = {
            'success': False,
            'document_id': f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'pages': [],
            'metadata': {},
            'parse_chain': [],
            'error': None,
            'fallback_used': False
        }
        
        try:
            # Step 1: Detect file type
            file_type_info = detect_file_type(file_path)
            parse_chain.append(f"file_detection: {file_type_info['type']}")
            
            # Step 2: Route to appropriate parser
            if is_drawing(file_path):
                print("  -> Using Drawing Parser (P&ID)")
                try:
                    parsed = drawing_parser.parse_drawing(file_path)
                    if parsed.get('error'):
                        # If drawing parser fails, we still try OCR on text
                        print(f"  [WARNING] Drawing parser had issues: {parsed['error']}")
                        parse_chain.append(f"drawing_partial_fail: {parsed['error']}")
                        # Get text via OCR
                        text_parsed = scanned_ocr.parse_scanned(file_path)
                        if 'error' in text_parsed and text_parsed.get('fallback_used'):
                            raise Exception(text_parsed['error'])
                        result['pages'] = text_parsed['pages']
                        result['metadata'] = text_parsed['metadata']
                    else:
                        result['pages'] = parsed['pages']
                        result['metadata'] = parsed['metadata']
                        # Add special drawing metadata
                        result['equipment_tags'] = parsed.get('equipment_tags', [])
                    result['parse_chain'] = parse_chain + ['drawing_paddleocr_or_vision']
                except Exception as draw_error:
                    print(f"  [WARNING] Drawing parser failed: {draw_error}")
                    # Ultimate fallback: regular OCR
                    parsed = scanned_ocr.parse_scanned(file_path)
                    if 'error' in parsed and parsed.get('fallback_used'):
                        raise Exception(parsed['error'])
                    result['pages'] = parsed['pages']
                    result['metadata'] = parsed['metadata']
                    result['parse_chain'] = parse_chain + ['ocr_fallback_after_drawing_fail']
                    result['fallback_used'] = True
            
            elif file_type_info['type'] == 'clean_text':
                print("  -> Using Clean Text Parser")
                parsed = clean_text.parse_clean_text(file_path)
                result['pages'] = parsed['pages']
                result['metadata'] = parsed['metadata']
                result['parse_chain'] = parse_chain + ['clean_text_pymupdf']
                result['fallback_used'] = parsed.get('parse_method') != 'pymupdf'
                
            elif file_type_info['type'] == 'scanned':
                print("  -> Using Scanned OCR Parser")
                try:
                    parsed = scanned_ocr.parse_scanned(file_path)
                    if 'error' in parsed and parsed.get('fallback_used'):
                        # If OCR is missing/TesseractNotFoundError
                        raise Exception(parsed['error'])
                    result['pages'] = parsed['pages']
                    result['metadata'] = parsed['metadata']
                    result['parse_chain'] = parse_chain + ['scanned_ocr_tesseract']
                except Exception as ocr_error:
                    print(f"  [WARNING] Tesseract failed: {ocr_error}")
                    parse_chain.append(f"ocr_failed: {str(ocr_error)}")
                    
                    # Fallback to LayoutLM (if available)
                    try:
                        print("  -> Falling back to LayoutLMv3...")
                        parsed = layout_parser.parse_layout(file_path)
                        if 'error' in parsed and parsed.get('fallback_used'):
                            raise Exception(parsed['error'])
                        result['pages'] = parsed['pages']
                        result['metadata'] = parsed['metadata']
                        result['parse_chain'] = parse_chain + ['layoutlmv3_fallback']
                        result['fallback_used'] = True
                    except Exception as layout_error:
                        raise Exception(f"All OCR methods failed: {layout_error}")
            
            else:
                # Unknown file type
                raise Exception(f"Unsupported file type or extension: {file_type_info.get('reason', 'unknown')}")
            
            result['success'] = True
            if not result.get('parse_chain'):
                result['parse_chain'] = parse_chain
            
            # Log success
            print(f"[SUCCESS] Parse complete! Pages: {len(result['pages'])}")
            
            # Save parsed result
            self._save_parsed_result(result, file_path)
            
            return result
            
        except Exception as e:
            # Ultimate failure: Return graceful error
            result['success'] = False
            result['error'] = str(e)
            result['parse_chain'] = parse_chain
            print(f"[ERROR] Parse failed: {e}")
            return result
    
    def _save_parsed_result(self, result, file_path):
        """Save the parsed result as JSON for later use"""
        try:
            # Use path relative to current module / base dir
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, "data", "parsed")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save as JSON
            output_path = os.path.join(output_dir, f"{result['document_id']}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, default=str, indent=2)
            
            print(f"  [INFO] Saved to: {output_path}")
        except Exception as e:
            print(f"  [WARNING] Could not save parsed result: {e}")
