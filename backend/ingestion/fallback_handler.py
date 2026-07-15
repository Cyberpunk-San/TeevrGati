def get_user_friendly_message(parse_result):
    """
    Translate technical errors into user-friendly feedback.
    """
    if parse_result.get('success'):
        return {
            'status': 'success',
            'message': f"✅ Document parsed successfully! Found {len(parse_result.get('pages', []))} pages.",
            'fallback_warning': None
        }
    
    # Failed cases
    error_msg = parse_result.get('error', 'Unknown error')
    
    if 'tesseract' in error_msg.lower():
        return {
            'status': 'error',
            'message': '🔧 OCR Engine (Tesseract) is not installed. Please install it or upload a text-based PDF.',
            'suggestion': 'Install Tesseract: brew install tesseract (Mac) / apt-get install tesseract-ocr (Linux) or check your system Path.'
        }
    
    if 'corrupt' in error_msg.lower() or 'damaged' in error_msg.lower():
        return {
            'status': 'error',
            'message': '📄 This document appears to be corrupted or damaged. Please re-upload a clean copy.',
            'suggestion': 'Try saving the PDF from your source application again.'
        }
    
    if 'unsupported' in error_msg.lower():
        return {
            'status': 'error',
            'message': '📎 Unsupported file type. Currently we support PDFs and image files.',
            'suggestion': 'Please convert your document to PDF or PNG/JPG and try again.'
        }
    
    # Generic fallback
    return {
        'status': 'error',
        'message': f'⚠️ Could not parse this document: {error_msg[:200]}',
        'suggestion': 'Try uploading a cleaner version or contact support.'
    }
