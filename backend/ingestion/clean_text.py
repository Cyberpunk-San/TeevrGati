import fitz  # PyMuPDF
import pdfplumber

def parse_clean_text(file_path):
    """
    Primary: PyMuPDF (fast)
    Fallback: pdfplumber (better for tables)
    """
    results = {
        'pages': [],
        'metadata': {},
        'tables': [],
        'parse_method': 'pymupdf'
    }
    
    # Attempt 1: PyMuPDF
    try:
        doc = fitz.open(file_path)
        results['metadata'] = doc.metadata or {}
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            results['pages'].append({
                'page_num': page_num + 1,
                'text': text,
                'length': len(text)
            })
        
        doc.close()
        return results
        
    except Exception as e:
        # Fallback 1: pdfplumber (better for table detection)
        print(f"PyMuPDF failed: {e}. Falling back to pdfplumber...")
        try:
            with pdfplumber.open(file_path) as pdf:
                results['parse_method'] = 'pdfplumber'
                results['metadata'] = pdf.metadata or {}
                results['pages'] = [] # Reset pages list
                
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    tables = page.extract_tables()
                    if tables:
                        results['tables'].append({
                            'page_num': page_num + 1,
                            'tables': tables
                        })
                    results['pages'].append({
                        'page_num': page_num + 1,
                        'text': text,
                        'length': len(text)
                    })
            return results
            
        except Exception as e2:
            # Critical failure
            raise Exception(f"Both PyMuPDF and pdfplumber failed: {e2}")
