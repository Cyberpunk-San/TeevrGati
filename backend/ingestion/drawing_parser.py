import fitz
from PIL import Image
import re

# Initialize PaddleOCR once
ocr = None

def get_ocr():
    global ocr
    if ocr is None:
        # Lazy import paddleocr to prevent import crashes when it is not installed
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Angle classification for rotated docs
    return ocr

def parse_drawing(file_path):
    """
    Extracts equipment tags from P&IDs using PaddleOCR.
    Returns a list of {'tag': 'VLV-101', 'location': (x, y), 'context': 'text near box'}
    """
    results = {
        'pages': [],
        'metadata': {},
        'parse_method': 'paddleocr',
        'equipment_tags': [],
        'lines': []  # For future relationship mapping
    }
    
    try:
        paddle_ocr_instance = get_ocr()
        doc = fitz.open(file_path)
        results['metadata'] = doc.metadata or {}
        
        for page_num, page in enumerate(doc):
            # Render page to image
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Convert to path or pass img array/PIL to PaddleOCR
            # PaddleOCR.ocr can accept path or numpy array. Since we rendered to PIL, 
            # we should convert it to numpy array or save it as temporary file.
            # Convert PIL Image to numpy array:
            import numpy as np
            img_np = np.array(img)
            
            # PaddleOCR returns text with bounding boxes
            ocr_result = paddle_ocr_instance.ocr(img_np, cls=True)
            
            # Extract text and positions
            page_tags = []
            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    bbox = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    text = line[1][0]  # The actual text
                    confidence = line[1][1]
                    
                    # Simple heuristic: equipment tags are often alphanumeric with hyphens
                    # e.g., "P-101", "VLV-302", "COMP-01"
                    if re.match(r'^[A-Z]{2,4}-[0-9]{2,4}$', text):
                        page_tags.append({
                            'tag': text,
                            'bbox': bbox,
                            'confidence': confidence
                        })
            
            results['equipment_tags'].extend(page_tags)
            results['pages'].append({
                'page_num': page_num + 1,
                'tags': page_tags,
                'raw_ocr': ocr_result
            })
        
        doc.close()
        return results
        
    except Exception as e:
        return {
            'error': f'Drawing parsing failed: {e}',
            'fallback_used': True,
            'equipment_tags': []
        }
