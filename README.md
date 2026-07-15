# 🏭 TeevrGati: Multi-Agent Closed-Loop Industrial Intelligence & Self-Healing Graph Portal

**TeevrGati** (तीव्र गति - meaning *High Velocity*) is a closed-loop cyber-physical intelligence platform built for modern industrial assets. It bridges manual operating procedures (SOPs), live vibration waveforms, and operator tacit knowledge in a single, self-healing diagnostics co-pilot.

---

## 👁️ System Architecture

TeevrGati connects three distinct industrial domains to manage asset health and safety:

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
│  (SOP Manual text)   │                                    │  (FFT & IsolationF)  │
└──────────────────────┘                                    └──────────────────────┘
           │                                                           │
           └───────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    Conflict Detector Layer  │
                    └─────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
              [No Conflict]                  [Conflict!]
                    │                             │
                    ▼                             ▼
             ┌──────────────┐             ┌────────────────────────┐
             │ Synthesized  │             │   Resolution Engine    │
             │ Action Plan  │             │   • Auto-Decision      │
             └──────────────┘             │   • Human Override     │
                                          └────────────────────────┘
                                                      │
                                                      ▼
                                          ┌────────────────────────┐
                                          │   Self-Healing Graph   │
                                          │   • Outdate old nodes      │
                                          │   • REPLACED_BY links      │
                                          └────────────────────────┘
```

---

## ⚡ Core Features

### 1. Ingestion Pipeline
* **Visual Router**: Automatically classifies documents and selects the best parsing engine.
* **Complex Tabular Parsing**: Extracts technical parameters using LayoutLMv3 layout detection.
* **Engineering Drawings (P&ID)**: Extracts structured equipment numbers and layout links using Gemini Vision API with PyMuPDF/regex fallback (no PaddleOCR dependency on Python 3.14).
* **Synthetic Refinery Data**: Pre-loaded with synthetic BPCL Mathura Refinery data (Pump P-201 manuals, SOPs with deliberate contradictions, SAP PM work orders, RCA reports).

### 2. Physical Waveform Simulator
* **4-Class Bearing Fault Model**: Trained on synthetic CWRU-like bearing data (Healthy, Inner Race Fault, Outer Race Fault, Ball Defect) with 100% test accuracy.
* **Frequency Analysis**: Computes Fast Fourier Transforms (FFT) to extract spectral peaks.
* **Envelope Analysis**: Applies the Hilbert Transform for bearing fault isolation.

### 3. Truth Engine & Self-Healing Graph
* **Conflict Resolution**: Resolves discrepancies between old manuals (e.g. 2019 SOP vs 2024 SOP) and live sensor metrics (prioritizing live physics with confidence $\ge 80\%$).
* **Multi-Agent Debate**: Orchestrates a debate between Historian (RAG+KG), Physicist (Sensor Telemetry), and Operator (Tacit Knowledge) agents for consensus.
* **Self-Healing Mechanics**: Updates outdated nodes, captures reconciliation timestamps, and links outdated documents to current rules with `REPLACED_BY` relationships.

### 4. Advanced UX & Field Utilities
* **🔔 Live Push Notifications**: Proactive `ntfy.sh` integration for real-time mobile alerts when anomalous faults are detected.
* **🎤 Tacit Knowledge Interview**: `/api/tacit/interview` API endpoint provides a 5-question guided exit interview to capture unwritten operator knowledge.
* **🛡️ Safety Compliance Gap Detection**: Verifies action plans against safety protocols (e.g., OISD-105) and displays warning alerts for missing safety steps.
* **📈 Knowledge Benchmark**: Comprehensive 15-question suite measuring RAG vs Keyword retrieval latency and recall.

---

## 📁 Repository Directory Structure

```
teevrgati/
├── backend/
│   ├── compliance/
│   │   └── gap_detector.py      # Regulatory safety checking
│   ├── brain/
│   │   └── unified_brain.py     # Routes queries to Vector RAG and Knowledge Graph
│   ├── ingestion/
│   │   ├── parser.py            # Routing parser
│   │   ├── clean_text.py        # Digital PDF parser
│   │   └── drawing_parser.py    # Gemini Vision API schematic parsing (PaddleOCR removed)
│   ├── kg/
│   │   └── knowledge_graph.py   # NetworkX ontology builder & graph database
│   ├── luigi_ears/
│   │   ├── vibration_tools.py   # Hilbert Transform envelope & FFT analyzer
│   │   └── work_order_gen.py    # LOTO safety work order generation
│   ├── orchestrator/
│   │   ├── orchestrator.py      # Core agent routing, multi-agent debate, & conflict detection
│   │   ├── push_engine.py       # ntfy.sh real-time push notifications
│   │   ├── resolution_engine.py # Auto-resolution & self-healing rules
│   │   └── tacit_agent.py       # Operator tacit knowledge capture
│   └── server.py                # Zero-dependency REST API server (Port 8000)
├── benchmark.py                 # 15-Question evaluation suite
├── frontend-next/               # Next.js React TSX GSAP Web Portal
│   ├── app/
│   │   ├── components/          # Reusable visual components (Voice, Badges, Drop, Paths)
│   │   ├── graph/               # Dedicated interactive SVG graph visualization
│   │   ├── ingest/              # Document uploading & freshness stats
│   │   ├── maintenance/         # Generated work orders & alert dispatch logs
│   │   ├── page.tsx             # Main Diagnostics Console
│   │   └── layout.tsx           # Global layout & sidebar layout mount
│   └── package.json
└── requirements.txt             # Python requirements
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have the following installed on your system:
* Python 3.9+
* Node.js 18+

### 2. Backend Installation
1. Navigate to the project root directory.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the backend database, RAG vector index, and sample data.

### 3. Frontend Installation
1. Navigate to the frontend directory:
   ```bash
   cd frontend-next
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
### 4. Configuration & Model Customization
To configure the API server or customize the AI models:
1. Open the `.env` file at the root of the project.
2. Customize the environment variables to control model routing:
   * **Fine-Tuned Model Customization**: Specify your custom fine-tuned model ID via:
     ```env
     TEEVRGATI_FINE_TUNED_MODEL=ft:gpt-3.5-turbo-xxxx
     ```
     *(The backend automatically detects and prioritizes any model specified via `TEEVRGATI_FINE_TUNED_MODEL`, `FINE_TUNED_MODEL`, or `OPENAI_MODEL` prefixed with `ft:` when the appropriate API key is present).*
   * **Standard LLM Credentials**:
     ```env
     GEMINI_API_KEY=your-gemini-api-key
     OPENAI_API_KEY=your-openai-api-key
     HF_TOKEN=your-huggingface-token
     ```
   * **Fallback Hierarchy**: The backend first attempts the configured fine-tuned model. If not configured or if execution fails, it falls back to:
     1. **Gemini** (`gemini-1.5-flash`)
     2. **OpenAI** (defaults to `gpt-3.5-turbo` or the custom `OPENAI_MODEL`)
     3. **Hugging Face** (defaults to `mistralai/Mistral-7B-Instruct-v0.2` or the custom `HF_MODEL`)

---

## 🚀 Running the Platform

### Step 1: Start the API Server
In a terminal, run the Python API gateway:
```bash
python backend/server.py
```
*The API gateway will start on **`http://localhost:8000`**.*

### Step 2: Start the Next.js Web App
Open a second terminal, navigate to the frontend directory, and run:
```bash
cd frontend-next
npm run dev
```
*The React portal will start on **`http://localhost:3000`**.*

---

## 🧪 Step-by-Step Demo Flow

1. **Ask a Query**: Open the web app and enter:
   > *"Pump P-201 is vibrating loudly. What could be wrong?"*
2. **Observe the Debate & Conflict**: The console displays the **Multi-Agent Consensus Debate** dialogue where the Historian (manual), Physicist (live vibration envelope BPFO/RMS anomaly signature), and Operator (captured tacit log tweaks) voice their individual assessments before arriving at a consensus.
3. **Execute Resolution**: Choose to apply the resolution. The Truth Engine updates the Knowledge Graph, marking the manual node as `outdated` and displaying the **Multi-Hop Traversal Proof** route.
4. **Inspect Graph**: Navigate to the **Self-Healing Graph** tab to verify that outdated manual nodes have turned dim gray and that a green dashed `REPLACED_BY` link points to the active truth rule.
5. **Verify Ingestion**: Navigate to the **SOP Ingest** tab. Drop a new PDF document into the dropzone to watch the parser parse it and automatically refresh the **Freshness Inventory** sidebar.
6. **Monitor Compliance & Performance**: Navigate to the **Compliance & Metrics** tab to review real-time audit benchmarks (latency, NER extraction accuracy) and inspect regulatory safety gap alerts.
7. **Toggle UI Theme**: Use the Sun/Moon toggle at the bottom of the sidebar to swap themes (from dark to high-visibility light theme).
8. **Export Report**: On the main Diagnostics Console, click **Export Report PDF** to open the browser print dialog and save a clean safety report.
