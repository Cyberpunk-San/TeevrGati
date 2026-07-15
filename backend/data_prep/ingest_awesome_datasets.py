import os
import json
import sys

# Ensure project root workspace is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from backend.brain.unified_brain import UnifiedBrain

def ingest_awesome_catalog():
    """
    Parses metadata JSONs from awesome-industrial-datasets-master and 
    registers them in the TeevrGati Knowledge Graph and RAG vector store.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_dir = os.path.join(base_dir, "backend", "data", "vibration", "awesome-industrial-datasets-master", "json")
    
    if not os.path.exists(json_dir):
        print(f"[ERROR] Awesome Industrial Datasets catalog directory not found: {json_dir}")
        return
        
    brain = UnifiedBrain()
    
    # List all json files
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    print(f"Found {len(json_files)} industrial datasets to ingest.")
    
    success_count = 0
    # Ingest first 30 datasets to keep database size highly balanced for the demo, 
    # but customizable via environment.
    max_ingest = int(os.getenv('TEEVRGATI_MAX_DATASET_INGEST', '50'))
    
    for filename in json_files[:max_ingest]:
        path = os.path.join(json_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            name = data.get('Name', 'Unnamed Dataset')
            summary = data.get('Summary', '')
            domain = data.get('Domain', '')
            asset = data.get('Asset / Process', '')
            desc = data.get('Description', '')
            
            # Formulate text representation
            text = f"""
            INDUSTRIAL DATASET SPECIFICATION
            Dataset Name: {name}
            Domain Area: {domain}
            Asset Target: {asset}
            Summary Overview: {summary}
            Detailed Description: {desc}
            """
            
            doc_id = f"dataset_{os.path.splitext(filename)[0]}"
            
            # Format to mock document parse structure expected by UnifiedBrain
            parse_result = {
                'success': True,
                'document_id': doc_id,
                'pages': [
                    {
                        'page_num': 1,
                        'text': text.strip()
                    }
                ],
                'metadata': {
                    'title': name,
                    'format': 'JSON Catalog Entry',
                    'author': 'Awesome Industrial Datasets',
                    'category': domain
                }
            }
            
            brain.ingest_document(parse_result)
            success_count += 1
            print(f"[{success_count}] Successfully ingested dataset: {name}")
            
        except Exception as e:
            print(f"[ERROR] Failed to ingest {filename}: {e}")
            
    print(f"\n[SUCCESS] Ingested {success_count} industrial catalog items into the unified brain.")

if __name__ == "__main__":
    ingest_awesome_catalog()
