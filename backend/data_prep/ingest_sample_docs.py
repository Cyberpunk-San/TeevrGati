"""
ingest_sample_docs.py — Ingest all BPCL synthetic PDFs into TeevrGati brain.
Run after generate_synthetic_data.py to populate ChromaDB + KG.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.orchestrator.orchestrator import Orchestrator
from backend.ingestion.parser import DocumentParser

# Always resolve relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "backend", "data", "sample")

PDF_FILES = [
    "pump_manual.pdf",
    "SOP_P201_Maintenance_v2019.pdf",
    "SOP_P201_Maintenance_v2024.pdf",
    "SOP_Compressor_C101_SafetyProcedure.pdf",
]

def main():
    print("🔄 Ingesting BPCL Mathura synthetic documents into TeevrGati brain...")
    orchestrator = Orchestrator()
    parser = DocumentParser()
    success_count = 0

    for filename in PDF_FILES:
        path = os.path.join(SAMPLE_DIR, filename)
        if not os.path.exists(path):
            print(f"  ⚠️  Not found, skipping: {filename}")
            continue

        print(f"  📄 Parsing: {filename}")
        result = parser.parse(path)

        if result.get("success"):
            orchestrator.brain.ingest_document(result)
            pages = len(result.get("pages", []))
            print(f"  ✅  Ingested: {filename} ({pages} pages)")
            success_count += 1
        else:
            print(f"  ❌  Failed: {filename} — {result.get('error', 'unknown error')}")

    orchestrator.brain.save()
    print(f"\n✅ Done. {success_count}/{len(PDF_FILES)} documents ingested.")
    print("   ChromaDB and Knowledge Graph updated.")

if __name__ == "__main__":
    main()
