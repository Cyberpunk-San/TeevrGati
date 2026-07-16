# TeevrGati: Multi-Agent Closed-Loop Industrial Intelligence & Self-Healing Graph Portal

**TeevrGati** (तीव्र गति — *High Velocity*) is a closed-loop cyber-physical intelligence platform for industrial assets. It bridges SOPs, standards, live vibration analysis, and operator tacit knowledge in a self-healing diagnostics co-pilot.

**Vertical / persona:** BPCL Mathura Refinery · Pump P-201 maintenance & safety team  
**Built for:** ET AI Hackathon 2026 · Problem Statement 8 (Industrial Knowledge Intelligence)

---

## System Architecture

```
                                  [Operator Query]
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │   TeevrGati API Server (Port 8000)    │
                     └───────────────────────────────────────┘
                                   │           │
           ┌───────────────────────┘           └───────────────────────┐
           ▼                                                           ▼
┌──────────────────────┐                                    ┌──────────────────────┐
│  Vector/Chroma RAG   │                                    │  vibration_tools.py  │
│  SOPs + Standards    │                                    │  FFT + Hilbert + RF  │
└──────────────────────┘                                    └──────────────────────┘
           │                                                           │
           └───────────────────────┬───────────────────────────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │    Conflict Detector Layer  │
                    └──────────────┬──────────────┘
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
       [No Conflict]                              [Conflict!]
              │                                         │
              ▼                                         ▼
       ┌──────────────┐                      ┌────────────────────────┐
       │ Synthesized  │                      │   Resolution Engine    │
       │ Action Plan  │                      │   Auto + Human Override│
       └──────────────┘                      └───────────┬────────────┘
                                                         ▼
                                              ┌────────────────────────┐
                                              │   Self-Healing Graph   │
                                              │   REPLACED_BY links    │
                                              └────────────────────────┘
```

---

## Core Features

### 1. Ingestion Pipeline
* **Visual Router**: Classifies documents and selects the best parsing engine.
* **Layout / OCR / Vision**: LayoutLMv3, Tesseract, Gemini Vision for P&IDs (PaddleOCR optional via isolated venv).
* **Corpus**: Synthetic BPCL Mathura SOPs (deliberate contradictions) plus regulatory/standards PDFs (Factories Act, ISO 10816, API 610/670, PESO).

### 2. Bearing Fault Classifier (Physicist)
* **4-class RandomForest** trained on **real CWRU** waveforms (Kaggle `brjapon/cwru-bearing-datasets`):
  Healthy · Inner Race Fault · Outer Race Fault · Ball Defect
* **Test accuracy: 92.6%** (held-out windows from real `.mat` signals — not synthetic clusters)
* **Signal tools**: FFT spectral peaks, Hilbert envelope analysis, ISO 10816-3 zone scoring

### 3. Truth Engine & Self-Healing Graph
* Conflict detection between SOPs (e.g. 2019 vs 2024 torque / LOTO) and live physics
* Multi-agent debate: Historian (RAG+KG) · Physicist · Operator (tacit)
* Graph self-heal with `REPLACED_BY` edges and reconciliation timestamps

### 4. Field Utilities
* Proactive `ntfy.sh` push / shift briefing
* Tacit knowledge exit interview (`/api/tacit/interview`)
* Compliance gap checks against safety clauses
* 15-question grounded knowledge benchmark vs keyword baseline

---

## Measured Results (latest)

| Metric | Value |
|--------|-------|
| Bearing RF (real CWRU) | **92.6%** test accuracy |
| RAG entity recall | **82.7%** |
| Keyword baseline recall | 62.1% |
| Recall gain | **+20.5 pp** |
| Avg TeevrGati latency | ~2.8 s / query |

Results file: `backend/data/benchmark/benchmark_results.json`  
Model card: `backend/models/model_card.json`

---

## Repository Layout

```
teevrgati/
├── backend/
│   ├── compliance/gap_detector.py
│   ├── brain/unified_brain.py
│   ├── ingestion/          # PDF / OCR / drawing parsers
│   ├── kg/knowledge_graph.py
│   ├── luigi_ears/         # FFT, envelope, work orders
│   ├── models/             # predictive_model.py + model_card.json (*.pkl gitignored)
│   ├── data_prep/
│   │   ├── convert_cwru_kaggle.py   # .mat → cwru_features.csv
│   │   ├── train_cwru.py            # retrain 4-class RF
│   │   └── ingest_sample_docs.py    # SOPs + standards → Chroma/KG
│   ├── orchestrator/       # agents, conflict, push, tacit
│   └── server.py           # FastAPI :8000
├── benchmark.py
├── frontend-next/          # Next.js portal :3000
└── requirements.txt
```

---

## Installation & Setup

### Prerequisites
* Python 3.9+
* Node.js 18+

### Backend
```bash
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend-next && npm install
```

### Environment (`.env`)
```env
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
HF_TOKEN=your-huggingface-token
# optional
TEEVRGATI_FINE_TUNED_MODEL=ft:gpt-3.5-turbo-xxxx
```

**LLM fallback order:** fine-tuned → Gemini (`gemini-2.0-flash` / `1.5-flash`) → OpenAI → Hugging Face

Use real API keys for live debate/synthesis. RAG + vibration ML still work without them (heuristic fallback).

---

## Running

```bash
# optional P&ID OCR (Python 3.10 venv)
bash scripts/setup_paddleocr.sh

# API
source venv/bin/activate
python backend/server.py          # http://localhost:8000

# UI
cd frontend-next && npm run dev   # http://localhost:3000
```

---

## Retrain / Re-ingest

### CWRU bearing model
```bash
# Place Kaggle dataset under backend/data/vibration/ (cwru_raw/*.mat)
# or: kaggle datasets download -d brjapon/cwru-bearing-datasets -p backend/data/vibration --unzip

python backend/data_prep/convert_cwru_kaggle.py
python backend/data_prep/train_cwru.py
```

Raw `.mat` / `.npz` files are gitignored (large). Features CSV + convert/train scripts are in-repo.

### Standards + SOPs into RAG/KG
```bash
# Drop PDFs into backend/data/sample/
python backend/data_prep/ingest_sample_docs.py
python benchmark.py
```

**Citation:** Case Western Reserve University Bearing Data Center; Kaggle mirror [brjapon/cwru-bearing-datasets](https://www.kaggle.com/datasets/brjapon/cwru-bearing-datasets).

---

## Demo Flow

1. Query: *"Pump P-201 is vibrating loudly. What could be wrong?"*
2. Watch Agent Pipeline: Historian → Simulator → Conflict → Synthesis
3. Resolve SOP vs physics conflict (Trust Physics / Trust SOP / Ask Engineer)
4. Inspect KG Graph (`REPLACED_BY` edges)
5. Live-ingest a new PDF on **Ingest SOP**
6. Show metrics: **CWRU 92.6%** · **RAG +20.5 pp vs keyword**

---

## License / Attribution

* Application code: project authors
* CWRU vibration data: Case Western Reserve University Bearing Data Center (via public Kaggle mirror)
* Standards excerpts: use only documents you are licensed to redistribute
