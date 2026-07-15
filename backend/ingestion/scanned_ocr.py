import os
import pytesseract
from PIL import Image
import fitz  # To extract images from PDF

def parse_scanned(file_path):
    """
    Converts each PDF page to image, runs Tesseract OCR.
    Also handles direct image files.
    """
    results = {
        'pages': [],
        'metadata': {},
        'parse_method': 'tesseract'
    }
    
    # Check if the file is a PDF or a raw image
    _, ext = os.path.splitext(file_path.lower())
    
    try:
        if ext == '.pdf':
            doc = fitz.open(file_path)
            results['metadata'] = doc.metadata or {}
            
            for page_num, page in enumerate(doc):
                # Render page to image (DPI = 300 for good OCR)
                pix = page.get_pixmap(dpi=300)
                # Convert to PIL Image using frombytes
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Run Tesseract
                try:
                    text = pytesseract.image_to_string(img, lang='eng')
                except pytesseract.TesseractNotFoundError:
                    doc.close()
                    return {
                        'error': 'Tesseract OCR is not installed. Please install it and try again.',
                        'fallback_used': True,
                        'pages': []
                    }
                
                results['pages'].append({
                    'page_num': page_num + 1,
                    'text': text,
                    'length': len(text)
                })
            
            doc.close()
            return results
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            # Handle raw image directly
            img = Image.open(file_path)
            try:
                text = pytesseract.image_to_string(img, lang='eng')
            except pytesseract.TesseractNotFoundError:
                return {
                    'error': 'Tesseract OCR is not installed. Please install it and try again.',
                    'fallback_used': True,
                    'pages': []
                }
            
            results['pages'].append({
                'page_num': 1,
                'text': text,
                'length': len(text)
            })
            return results
        else:
            raise ValueError(f"Unsupported format for OCR: {ext}")
            
    except Exception as e:
        raise Exception(f"Scanned PDF parsing failed: {e}")
