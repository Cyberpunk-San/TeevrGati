import streamlit as st
import os
import sys

# Ensure backend is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.ingestion.parser import DocumentParser
from backend.ingestion.fallback_handler import get_user_friendly_message
from backend.orchestrator.orchestrator import Orchestrator
from frontend.components.conflict_display import render_conflict
from frontend.components.graph_viz import render_graph_viz

# Page Configuration with curated premium look
st.set_page_config(
    page_title="Industrial Cortex | Autonomous Brain & Diagnostics",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling via CSS injection
st.markdown("""
<style>
    /* Main Layout Aesthetics */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
        text-align: center;
        border-left: 5px solid #00c6ff;
    }
    .header-card h1 {
        color: #ffffff;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    .header-card p {
        color: #d1d5db;
        font-size: 1.1rem;
        margin-bottom: 0;
    }

    /* Container Blocks */
    .styled-container {
        background-color: #1a1f2c;
        border: 1px solid #2e374a;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Custom Badges */
    .custom-badge {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div class="header-card">
    <h1>🏭 Industrial Cortex - Unified Intelligence</h1>
    <p>Document Ingestion Pipeline linked with Physics-based Vibration Diagnostics & Multi-Hop Ontologies.</p>
</div>
""", unsafe_allow_html=True)

# Initialize Orchestrator once
@st.cache_resource
def get_orchestrator():
    return Orchestrator()

# Set up tabs
tab1, tab2 = st.tabs(["📥 Document Ingestion", "🧠 Industrial Brain & Conflict Detector"])

# Sidebar for file upload (used primarily in Tab 1)
with st.sidebar:
    st.markdown("### 📤 Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        key="pdf_uploader",
        help="Supports text PDFs, scanned documents, and engineering drawings"
    )
    
    temp_path = None
    if uploaded_file:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw_dir = os.path.join(base_dir, "backend", "data", "raw")
        os.makedirs(raw_dir, exist_ok=True)
        temp_path = os.path.join(raw_dir, uploaded_file.name)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ Uploaded: {uploaded_file.name}")

# --- TAB 1: Document Ingestion ---
with tab1:
    if uploaded_file and temp_path:
        st.markdown('<div class="styled-container">', unsafe_allow_html=True)
        st.subheader(f"🔍 Parsing: {uploaded_file.name}")
        
        with st.spinner("Routing and extracting content..."):
            parser = DocumentParser()
            result = parser.parse(temp_path)
            
            # Ingest into Unified Brain if parser was successful
            if result.get('success'):
                orchestrator = get_orchestrator()
                orchestrator.brain.ingest_document(result)
                st.success("🧠 Content parsed and loaded into Knowledge Graph & Vector Index!")
            
            feedback = get_user_friendly_message(result)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📄 Parse Results")
            if result.get('success'):
                st.info(feedback['message'])
                
                with st.expander("🔧 Parse Chain (Technical Details)", expanded=True):
                    for step in result.get('parse_chain', []):
                        st.code(step, language="bash")
                
                st.subheader(f"📖 Pages ({len(result.get('pages', []))})")
                for page in result.get('pages', [])[:3]:
                    with st.expander(f"Page {page.get('page_num', '?')}"):
                        st.text(page.get('text', '')[:1000] + ("..." if len(page.get('text', '')) > 1000 else ""))
                
                if len(result.get('pages', [])) > 3:
                    st.caption(f"Showing first 3 pages of {len(result['pages'])} pages total.")
            else:
                st.error(feedback['message'])
                if feedback.get('suggestion'):
                    st.info(f"💡 {feedback['suggestion']}")
        
        with col2:
            st.subheader("📊 Ingestion Statistics")
            st.metric("Pages Detected", len(result.get('pages', [])))
            st.metric("Pipeline Status", "✅ INGESTED" if result.get('success') else "❌ FAILED")
            if result.get('equipment_tags'):
                st.metric("Equipment Tags Extracted", len(result['equipment_tags']))
                st.write(", ".join([tag['tag'] for tag in result['equipment_tags']]))
            if result.get('fallback_used'):
                st.warning("⚡ Fallback OCR triggered")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="styled-container" style="text-align: center; padding: 4rem 2rem;">
            <h3>👈 Upload a PDF document in the sidebar to begin ingestion.</h3>
            <p>Documents are parsed, mapped to our Equipment Ontology, and indexed for semantic search.</p>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: Industrial Brain & Conflict Detector ---
with tab2:
    st.header("🧠 Diagnostic Co-Pilot & Detective Mode")
    st.write("Ask queries about specific equipment (e.g. Pump P-201) to search RAG index, traverse the multi-hop graph, run physics checks, and detect engineering conflicts.")
    
    query_input = st.text_input(
        "Enter Maintenance Query:", 
        "Pump P-201 is vibrating loudly. What could be wrong?",
        help="Include equipment tags like P-201 to query the knowledge graph"
    )
    
    if st.button("Run Multi-Agent Diagnostics", type="primary"):
        with st.spinner("Retrieving document context, querying graph, running vibration simulation..."):
            orchestrator = get_orchestrator()
            
            # Auto-generate sample PDF and ingest it to guarantee results
            sample_pdf_path = "backend/data/sample/pump_manual.pdf"
            if not os.path.exists(sample_pdf_path):
                from backend.test_orchestrator import create_sample_pdf
                create_sample_pdf(sample_pdf_path)
                
                parser = DocumentParser()
                parse_result = parser.parse(sample_pdf_path)
                if parse_result['success']:
                    orchestrator.brain.ingest_document(parse_result)
            
            # Execute query through orchestrator
            result = orchestrator.process_query(query_input)
            st.session_state['query_result'] = result
            st.session_state['conflict_resolution'] = None
            if 'tacit_knowledge_saved' in st.session_state:
                del st.session_state['tacit_knowledge_saved']
    
    # Render results from session state
    if 'query_result' in st.session_state:
        result = st.session_state['query_result']
        
        # Display Agent logs
        with st.expander("📋 Agent In-Progress Log (Streaming Logs for Judges)", expanded=False):
            for entry in result.get('agent_log', []):
                color = "green" if entry['level'] == "INFO" else "orange" if entry['level'] == "WARNING" else "red"
                st.markdown(f"**[{entry['timestamp']}]** <span style='color:{color}; font-weight:bold;'>[{entry['level']}]</span> {entry['message']}", unsafe_allow_html=True)
        
        # Check for conflicts
        if result.get('conflict_detected') and st.session_state.get('conflict_resolution') is None:
            render_conflict(result['conflict_details'])
        else:
            # Display resolution choice if any
            if st.session_state.get('conflict_resolution'):
                res = st.session_state['conflict_resolution']
                st.info(f"💡 Resolved using: **{res.upper()}**")
                
                # Fetch details from session state
                res_details = st.session_state.get('resolution_details', {})
                healed_nodes = res_details.get('healed_nodes', [])
                
                if res == 'human' and res_details.get('structured_rule'):
                    struct_rule = res_details['structured_rule']
                    st.success("💾 **Captured Tacit Knowledge**")
                    col_t1, col_t2 = st.columns(2)
                    col_t1.metric("Extracted Rule Type", struct_rule['type'].upper().replace("_", " "))
                    col_t2.metric("Extraction Confidence", f"{struct_rule['confidence']:.0%}")
                    st.markdown(f"**Rule Text:** *\"{struct_rule['rule_text']}\"*")
                    st.caption(f"Linked new tacit rule node **{res_details.get('winner_id')}** to equipment tag **EQ_{result.get('asset_id', 'P-201')}** via `APPLIES_TO` relationship.")
                    
                if healed_nodes:
                    with st.expander("🩹 View Graph Self-Healing Details (Provenance)", expanded=True):
                        st.write("The system has reconciled the graph schema automatically:")
                        for node in healed_nodes:
                            st.write(f"- Updated node **{node}** status to `OUTDATED`")
                        st.write(f"- Linked outdated documents to winner node **{res_details.get('winner_id')}** via `REPLACED_BY` relationships.")
            
            # Display main answer
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📝 Diagnosis & Hypotheses")
                st.markdown(result.get('final_answer', 'No answer synthesized.'))
                
                # Display hypotheses list
                with st.expander("🔬 View Alternate Hypotheses"):
                    for idx, hyp in enumerate(result.get('hypotheses', [])):
                        st.markdown(f"**{idx+1}. {hyp['cause']}**")
                        st.write(f"- Confidence: {hyp['confidence']:.0%}")
                        st.write(f"- Evidence: {hyp['evidence']}")
            
            with col2:
                # Physics result details
                phys = result.get('physics_result')
                if phys:
                    st.subheader("📊 Physics Assessment")
                    st.metric("Diagnosis", phys.get('fault_type', 'Normal'))
                    
                    sev = phys.get('severity', 'Normal')
                    st.metric("Vibration Severity", sev)
                    
                    if sev in ['Critical', 'Alert', 'High']:
                        st.error(f"🚨 Recommendation: {phys.get('recommendation', 'Immediate inspection needed')}")
                    elif sev == 'Warning':
                        st.warning(f"⚠️ Recommendation: {phys.get('recommendation', 'Schedule review')}")
                    else:
                        st.success(f"✅ Recommendation: {phys.get('recommendation', 'Normal parameters')}")
            
            # Work order details if created
            wo = result.get('work_order')
            if wo:
                st.divider()
                st.subheader("🛠️ Generated Maintenance Work Order")
                
                col_wo1, col_wo2, col_wo3 = st.columns(3)
                col_wo1.metric("Work Order ID", wo['id'])
                col_wo2.metric("Priority", wo['priority'])
                col_wo3.metric("Est. Labor", f"{wo['labor_estimate_hours']} Hours")
                
                st.markdown(f"**Description:** {wo['description']}")
                st.markdown(f"**Required Parts:** {', '.join(wo['spare_parts_required'])}")
                
                st.markdown("**Instructions:**")
                for step in wo['instructions']:
                    st.markdown(f"- {step}")
                
                st.markdown("**Safety Protocols:**")
                for rule in wo['safety_requirements']:
                    st.markdown(f"- ⚠️ {rule}")
            
            # Proactive alerts
            alerts = result.get('proactive_alerts')
            if alerts:
                st.divider()
                st.subheader("📤 Proactive Push Notification Dispatch")
                st.info("The following real-time notifications were dispatched to field technicians:")
                for alert in alerts:
                    # Choose color based on alert type
                    if 'critical' in alert.get('type', ''):
                        st.error(f"🔔 **{alert['recipient']}** [{alert['title']}]: {alert['message']}")
                    elif 'safety' in alert.get('type', ''):
                        st.warning(f"⚠️ **{alert['recipient']}** [{alert['title']}]: {alert['message']}")
                    else:
                        st.info(f"ℹ️ **{alert['recipient']}** [{alert['title']}]: {alert['message']}")
                        
        # Render Knowledge Graph sub-graph (always visible if query has been executed)
        st.divider()
        orchestrator = get_orchestrator()
        render_graph_viz(orchestrator.brain.kg, result.get('asset_id') or "P-201")
