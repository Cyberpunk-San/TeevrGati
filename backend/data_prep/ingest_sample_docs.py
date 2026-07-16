"""
ingest_sample_docs.py — Ingest all BPCL synthetic PDFs + standards into TeevrGati brain.
Run after generate_synthetic_data.py to populate ChromaDB + KG.
"""
import sys, os, glob

# Always resolve relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from backend.orchestrator.orchestrator import Orchestrator
from backend.ingestion.parser import DocumentParser

SAMPLE_DIR = os.path.join(PROJECT_ROOT, "backend", "data", "sample")

# Prefer explicit order (SOPs first for conflict demo), then any other PDFs
PRIORITY_PDFS = [
    "pump_manual.pdf",
    "SOP_P201_Maintenance_v2019.pdf",
    "SOP_P201_Maintenance_v2024.pdf",
    "SOP_Compressor_C101_SafetyProcedure.pdf",
    "factories_act_excerpts.pdf",
    "iso_10816_summary.pdf",
    "api_610_excerpt.pdf",
    "api_670_excerpt.pdf",
    "peso_guidelines.pdf",
]

def list_pdfs():
    found = []
    for name in PRIORITY_PDFS:
        path = os.path.join(SAMPLE_DIR, name)
        if os.path.exists(path):
            found.append(name)
    # Pick up any extra PDFs dropped into sample/ or sample/standards/
    extras = []
    for pattern in ("*.pdf", "standards/*.pdf"):
        for path in glob.glob(os.path.join(SAMPLE_DIR, pattern)):
            rel = os.path.relpath(path, SAMPLE_DIR)
            if rel not in found:
                extras.append(rel)
    return found + sorted(extras)

def main():
    pdf_files = list_pdfs()
    print(f"🔄 Ingesting {len(pdf_files)} documents into TeevrGati brain...")
    orchestrator = Orchestrator()
    parser = DocumentParser()
    success_count = 0

    for filename in pdf_files:
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
    print(f"\n✅ Done. {success_count}/{len(pdf_files)} documents ingested.")
    print("   ChromaDB and Knowledge Graph updated.")

if __name__ == "__main__":
    main()
