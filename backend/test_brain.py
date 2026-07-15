"""
Test script for Phase 1.
Run: python backend/test_brain.py
"""

import os
import sys
import shutil

# Ensure backend is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ingestion.parser import DocumentParser
from backend.brain.unified_brain import UnifiedBrain

def create_sample_pdf(path):
    """Programmatically generate a sample PDF containing equipment tags, SOP references, people, dates, and regulations."""
    import fitz  # PyMuPDF
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    
    text = (
        "INDUSTRIAL EQUIPMENT DATASHEET AND PROCEDURES\n\n"
        "Document Ref: SOP-2023 / Section 4(12)\n"
        "Date of Issue: 2024-01-01\n"
        "Author: Sr. Engineer Rao\n"
        "Department: Maintenance and Safety\n\n"
        "1. Equipment Specifications:\n"
        "- Tag Name: Pump P-101 (Centrifugal pump for water transfer)\n"
        "- Alternate Designator: P/101\n"
        "- Operating Limit: Max speed 3000 RPM\n"
        "- Mounting Bolt Torque: Recommended torque for Pump P-101 is 45 Nm.\n\n"
        "2. Safety Procedures:\n"
        "- Before starting Pump P-101, ensure lockout-tagout is complete.\n"
        "- Governed by regulation OISD 105 and Section 4(12) of safety manual.\n"
        "- General guidelines follow Factory Act protocols.\n\n"
        "3. Incident Logs:\n"
        "- On 2024-01-01, an incident occurred where a seal failed on Pump P-101.\n"
        "- Sr. Engineer Rao inspected the unit and noticed a gap.\n"
        "- Resolved by maintenance technician J. Doe, who replaced the seals.\n"
    )
    
    # Draw textbox
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()
    print(f"[SUCCESS] Generated sample PDF at: {path}")

def test_ingestion_and_query():
    # Setup test file directories and clear old data for testing if necessary
    sample_dir = "backend/data/sample"
    sample_path = os.path.join(sample_dir, "pump_manual.pdf")
    
    # Ensure sample document exists
    if not os.path.exists(sample_path):
        print("[WARNING] Sample document not found. Generating one...")
        create_sample_pdf(sample_path)
    
    # Step 1: Parse a document
    print("\n--- Step 1: Parsing Document ---")
    parser = DocumentParser()
    parse_result = parser.parse(sample_path)
    if not parse_result['success']:
        print(f"[ERROR] Parse failed: {parse_result.get('error')}")
        return
    
    print(f"[SUCCESS] Parsed: {len(parse_result['pages'])} pages")
    
    # Step 2: Ingest into Brain
    print("\n--- Step 2: Ingesting into Unified Brain ---")
    brain = UnifiedBrain(
        kg_path="backend/data/kg/graph.json",
        db_path="backend/data/chroma_db"
    )
    
    # Reset vector collection to avoid duplicates
    try:
        brain.vector.reset()
        print("[SUCCESS] Vector index reset for testing")
    except Exception as e:
        print(f"[WARNING] Vector index reset failed (might be first run): {e}")
        
    doc_id = brain.ingest_document(parse_result)
    print(f"[SUCCESS] Ingested Document ID: {doc_id}")
    
    # Step 3: Query
    print("\n--- Step 3: Running Queries ---")
    queries = [
        "What is the recommended torque for Pump P-101?",
        "Show me all safety procedures related to the pump.",
        "What incidents involved the pump recently?"
    ]
    
    for query in queries:
        print(f"\n[QUERY] Query: {query}")
        result = brain.query(query)
        
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   KG Results: {'[SUCCESS]' if result['kg_results'] else '[FAIL]'}")
        
        # Display extracted entities
        entities = result.get('entities_found', {})
        eq_found = [eq['tag'] for eq in entities.get('equipment', [])]
        reg_found = [reg['reference'] for reg in entities.get('regulations', [])]
        pers_found = [p['name'] for p in entities.get('persons', [])]
        dates_found = [d['date'] for d in entities.get('dates', [])]
        
        print(f"   Entities Found:")
        print(f"     Equipment: {eq_found}")
        print(f"     Regulations: {reg_found}")
        print(f"     Persons: {pers_found}")
        print(f"     Dates: {dates_found}")
        
        # Display RAG results
        rag_results = result.get('rag_results', {})
        chunks = rag_results.get('results', [])
        print(f"   RAG Results: {len(chunks)} chunks retrieved")
        for idx, chunk in enumerate(chunks[:2]):
            print(f"     Chunk {idx+1}: {chunk['text'][:120]}...")
            
    # Step 4: Save state and verify it loads back
    print("\n--- Step 4: Saving and Reloading Brain ---")
    brain.save()
    print("[SUCCESS] Brain state saved")
    
    # Reload test
    reloaded_brain = UnifiedBrain(
        kg_path="backend/data/kg/graph.json",
        db_path="backend/data/chroma_db"
    )
    print("[SUCCESS] Reloaded UnifiedBrain successfully")
    
    # Test multi-hop retrieval
    print("\n--- Step 5: Multi-Hop Knowledge Graph Check ---")
    eq_context = reloaded_brain.get_equipment_context("P-101")
    if "error" not in eq_context:
        print("[SUCCESS] Multi-hop retrieval successful!")
        print(f"   Equipment: {list(eq_context['equipment'].keys())}")
        print(f"   Regulations count: {len(eq_context['regulations'])}")
        print(f"   Procedures count: {len(eq_context['procedures'])}")
        print(f"   Incidents count: {len(eq_context['incidents'])}")
        print(f"   Paths found:")
        for path in eq_context['paths']:
            print(f"     {path['from']} --({path['relation']})--> {path['to']}")
    else:
        print(f"[ERROR] Multi-hop context query failed: {eq_context['error']}")

if __name__ == "__main__":
    test_ingestion_and_query()
