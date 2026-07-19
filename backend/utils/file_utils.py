import os
import PyPDF2
from PIL import Image

try:
    import magic  # python-magic-bin
except ImportError:
    magic = None

# Supported image extensions — routed to the drawing/vision parser
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
IMAGE_MIMETYPES = {'image/png', 'image/jpeg', 'image/bmp', 'image/tiff', 'image/webp'}

def detect_file_type(file_path):
    """
    Returns dict with 'type': one of 'clean_text', 'scanned', 'drawing', or 'unknown'
    Images (PNG/JPG etc.) are returned as 'drawing' so they go to the Vision pipeline.
    """
    # Step 1: Validate file exists
    if not os.path.exists(file_path):
        return {'type': 'unknown', 'reason': f'File not found: {file_path}'}

    ext = os.path.splitext(file_path)[1].lower()

    # Step 2: Detect images by extension or MIME type
    is_image = ext in IMAGE_EXTENSIONS
    if not is_image and magic:
        try:
            mime = magic.from_file(file_path, mime=True)
            if mime in IMAGE_MIMETYPES or mime.startswith('image/'):
                is_image = True
        except Exception:
            pass

    if is_image:
        return {'type': 'drawing', 'reason': f'Image file ({ext}) routed to Vision pipeline'}

    # Step 3: Check for PDF
    is_pdf = False
    if magic:
        try:
            mime = magic.from_file(file_path, mime=True)
            if 'pdf' in mime.lower():
                is_pdf = True
        except Exception:
            if ext == '.pdf':
                is_pdf = True
    else:
        if ext == '.pdf':
            is_pdf = True

    if not is_pdf:
        return {'type': 'unknown', 'reason': f'Unsupported file type: {ext}. Supported: PDF, PNG, JPG, JPEG, BMP, TIFF'}

    # Step 4: Check for text layer (clean PDF vs scanned)
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            check_pages = int(os.getenv('TEEVRGATI_PDF_CHECK_PAGES', '2'))
            num_pages_to_check = min(check_pages, len(reader.pages))
            for page_num in range(num_pages_to_check):
                page = reader.pages[page_num]
                text += page.extract_text() or ""

        char_thresh = int(os.getenv('TEEVRGATI_PDF_TEXT_THRESH_CHARS', '100'))
        if len(text.strip()) > char_thresh:
            return {'type': 'clean_text', 'text_sample': text[:200]}
        else:
            return {'type': 'scanned', 'reason': f'No text layer detected (less than {char_thresh} characters)'}
    except Exception as e:
        return {'type': 'scanned', 'reason': f'Error reading text layer: {str(e)}'}

def is_drawing(file_path):
    """
    Returns True if the file is likely a P&ID or engineering drawing.
    Images are always treated as drawings. PDFs are checked by filename keyword.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # All image files are drawings
    if ext in IMAGE_EXTENSIONS:
        return True

    # Check if PDF filename contains drawing-related keywords
    keywords_str = os.getenv('TEEVRGATI_DRAWING_KEYWORDS', 'drawing,pid,p&id,layout,schematic,blueprint')
    drawing_keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    filename = os.path.basename(file_path).lower()
    for keyword in drawing_keywords:
        if keyword in filename:
            return True

    return False
