import os
import PyPDF2
from PIL import Image

try:
    import magic  # python-magic-bin
except ImportError:
    magic = None

def detect_file_type(file_path):
    """
    Returns: 'clean_text', 'scanned', 'drawing', or 'unknown'
    """
    # Step 1: Validate file exists
    if not os.path.exists(file_path):
        return {'type': 'unknown', 'reason': f'File not found: {file_path}'}

    # Step 2: Check MIME type using magic
    is_pdf = False
    if magic:
        try:
            mime = magic.from_file(file_path, mime=True)
            if 'pdf' in mime.lower():
                is_pdf = True
        except Exception as e:
            # Fallback to extension check if magic fails
            if file_path.lower().endswith('.pdf'):
                is_pdf = True
    else:
        if file_path.lower().endswith('.pdf'):
            is_pdf = True

    if not is_pdf:
        return {'type': 'unknown', 'reason': 'Only PDFs are supported in this demo'}
    
    # Step 3: Check for text layer (clean PDF vs scanned)
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            # Check first N pages only to keep it fast
            check_pages = int(os.getenv('TEEVRGATI_PDF_CHECK_PAGES', '2'))
            num_pages_to_check = min(check_pages, len(reader.pages))
            for page_num in range(num_pages_to_check):
                page = reader.pages[page_num]
                text += page.extract_text() or ""
        
        # If we got more than N characters, it's a clean text PDF
        char_thresh = int(os.getenv('TEEVRGATI_PDF_TEXT_THRESH_CHARS', '100'))
        if len(text.strip()) > char_thresh:
            return {'type': 'clean_text', 'text_sample': text[:200]}
        else:
            return {'type': 'scanned', 'reason': f'No text layer detected (less than {char_thresh} characters)'}
    except Exception as e:
        return {'type': 'scanned', 'reason': f'Error reading text layer: {str(e)}'}

def is_drawing(file_path):
    """
    Heuristic: If the PDF has lots of lines and boxes but little text,
    it's probably a P&ID or engineering drawing.
    """
    # Check if filename contains drawing-related keywords from environment
    keywords_str = os.getenv('TEEVRGATI_DRAWING_KEYWORDS', 'drawing,pid,p&id,layout,schematic,blueprint')
    drawing_keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    filename = os.path.basename(file_path).lower()
    for keyword in drawing_keywords:
        if keyword in filename:
            return True
    
    # Optional image analysis check could go here
    return False

