"""
Test script for Phase 2.
Run: python backend/test_orchestrator.py
"""

import os
import sys
import json
import re

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator.orchestrator import Orchestrator
from backend.ingestion.parser import DocumentParser

def clean_text_for_console(text):
    """Strip emojis to prevent character encoding issues on Windows consoles"""
    if not isinstance(text, str):
        return str(text)
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\u2700-\u27bf"
        "\u2600-\u26ff"
        "\ufe0f"
        "\u200d"
        "\U0001f000-\U0001ffff"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)

def create_sample_pdf(path):
    """Programmatically generate a sample PDF containing equipment P-201 metadata."""
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
        "- Tag Name: Pump P-201 (Centrifugal pump for water transfer)\n"
        "- Alternate Designator: P/201\n"
        "- Operating Limit: Max speed 3000 RPM\n"
        "- Mounting Bolt Torque: Recommended torque for Pump P-201 is 45 Nm.\n\n"
        "2. Safety Procedures:\n"
        "- Before starting Pump P-201, ensure lockout-tagout is complete.\n"
        "- Governed by regulation OISD 105 and Section 4(12) of safety manual.\n"
        "- General guidelines follow Factory Act protocols.\n\n"
        "3. Incident Logs:\n"
        "- On 2024-01-01, an incident occurred where a seal failed on Pump P-201.\n"
        "- Sr. Engineer Rao inspected the unit and noticed a gap.\n"
        "- Resolved by maintenance technician J. Doe, who replaced the seals.\n"
    )
    
    # Draw textbox
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()
    print(f"[SUCCESS] Generated sample PDF at: {path}")

def test_orchestrator():
    print("=" * 60)
    print("Phase 2 Test: Orchestrator + Conflict Detection")
    print("=" * 60)
    
    # Step 1: Initialize
    orchestrator = Orchestrator()
    
    # Step 2: Ingest a document (if not already done)
    parser = DocumentParser()
    sample_path = "backend/data/sample/pump_manual.pdf"
    
    if not os.path.exists(sample_path):
        create_sample_pdf(sample_path)
        
    parse_result = parser.parse(sample_path)
    if parse_result['success']:
        orchestrator.brain.ingest_document(parse_result)
        print("[SUCCESS] Document ingested")
    else:
        print(f"[ERROR] Document parsing failed: {parse_result.get('error')}")
        return
    
    # Step 3: Test queries
    test_queries = [
        "Pump P-201 is vibrating loudly. What could be wrong?",
        "What are the maintenance procedures for Pump P-201?",
        "Has there been any incidents with Pump P-201 recently?"
    ]
    
    for query in test_queries:
        print(f"\n[QUERY] Query: {query}")
        print("-" * 40)
        
        result = orchestrator.process_query(query)
        
        # Print summary
        print(f"[STATUS] Success: {result['success']}")
        print(f"[STATUS] Time: {result['execution_time']:.2f}s")
        
        if result.get('conflict_detected'):
            print(f"[CONFLICT] CONFLICT DETECTED!")
            print(clean_text_for_console(f"   {result['conflict_details']['description']}"))
            print(clean_text_for_console(f"   Human Question:\n{result.get('human_question', 'N/A')}"))
        else:
            print(f"[ANSWER] Final Answer:")
            print(clean_text_for_console(f"   {result.get('final_answer', 'No answer generated')}"))
        
        if result.get('work_order'):
            print(clean_text_for_console(f"[WO] Work Order: {result['work_order']['id']}"))
            print(clean_text_for_console(f"   Priority: {result['work_order']['priority']}"))
        
        if result.get('proactive_alerts'):
            print(clean_text_for_console(f"[ALERTS] Alerts: {len(result['proactive_alerts'])} sent"))
            for alert in result['proactive_alerts']:
                print(clean_text_for_console(f"     - Recipient: {alert['recipient']}: {alert['message']}"))
        
        # Show agent log (first few lines)
        print(f"\n[LOG] Agent Log (first 3 entries):")
        for entry in result.get('agent_log', [])[:3]:
            # Clean logging
            clean_message = clean_text_for_console(entry['message'])
            print(f"  [{entry['timestamp']}] [{entry['level']}] {clean_message}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Phase 2 Test Complete!")

if __name__ == "__main__":
    test_orchestrator()
