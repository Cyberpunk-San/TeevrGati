import streamlit as st

def render_conflict(conflict_details: dict):
    """
    Render the split-screen conflict display with human-in-the-loop interview agent.
    """
    st.warning("⚠️ **Discrepancy Detected between Standards and Real-Time Reality!**")
    st.markdown(f"*{conflict_details.get('description', 'Disagreement found between sources.')}*")
    
    # Render Automated Recommendation
    auto_res = conflict_details.get('auto_resolution')
    if auto_res:
        st.markdown(f"""
        <div style="background-color: #1e293b; border-left: 5px solid #00f5d4; padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem;">
            <h4 style="margin: 0; color: #00f5d4;">🤖 Truth Engine Recommendation</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; color: #e2e8f0;">
                Suggest resolving using <strong>{auto_res['winner'].upper()}</strong>:<br>
                <em>"{auto_res['reason']}"</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Document Standards")
        st.markdown(f"**Hypothesis:** {conflict_details.get('document_hypothesis', 'Unknown')}")
        st.markdown(f"**Confidence:** {conflict_details.get('document_confidence', 0.0):.0%}")
        st.markdown(f"*{conflict_details.get('sources', {}).get('documents', 'No evidence provided')}*")
        st.metric("Document Confidence", f"{conflict_details.get('document_confidence', 0.0):.0%}", delta="Low", delta_color="inverse")
    
    with col2:
        st.subheader("🔬 Live Physics Analysis")
        st.markdown(f"**Diagnosis:** {conflict_details.get('physics_result', 'Unknown')}")
        st.markdown(f"**Confidence:** {conflict_details.get('physics_confidence', 0.0):.0%}")
        st.markdown(f"*{conflict_details.get('sources', {}).get('physics', 'Deterministic analysis')}*")
        st.metric("Physics Confidence", f"{conflict_details.get('physics_confidence', 0.0):.0%}", delta="High", delta_color="normal")
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    # Use callback or direct logic
    # To prevent circular imports, we import Orchestrator inline
    from backend.orchestrator.orchestrator import Orchestrator
    orchestrator = Orchestrator()
    
    with col1:
        if st.button("✅ Auto-Resolve (Physics Wins)", use_container_width=True, type="primary"):
            resolve_result = orchestrator.resolve_conflict(st.session_state['query_result'], choice='physics')
            st.session_state['conflict_resolution'] = 'physics'
            st.session_state['resolution_details'] = resolve_result
            st.session_state['query_result']['agent_log'].extend(resolve_result['agent_log'])
            st.rerun()
    
    with col2:
        if st.button("📄 Auto-Resolve (Documents Win)", use_container_width=True):
            resolve_result = orchestrator.resolve_conflict(st.session_state['query_result'], choice='documents')
            st.session_state['conflict_resolution'] = 'documents'
            st.session_state['resolution_details'] = resolve_result
            st.session_state['query_result']['agent_log'].extend(resolve_result['agent_log'])
            st.rerun()
    
    with col3:
        if st.button("🔍 Interview Senior Engineer", use_container_width=True):
            st.session_state['show_interview'] = True
            st.rerun()
            
    # Show the interactive interview dialog below the split screen if activated
    if st.session_state.get('show_interview') and conflict_details.get('human_question'):
        st.markdown("---")
        st.markdown("### 🎙️ Tacit Knowledge Capture Form")
        st.info("System is now in **Interview Mode** to capture undocumented operator workarounds.")
        
        # Display the custom question from TacitKnowledgeAgent
        st.markdown(conflict_details['human_question'])
        
        tacit_resp = st.text_area(
            "Engineer's Response / Explanation:", 
            placeholder="Type standard or unwritten workaround details here (e.g. 'We upgraded the bearing, so we tighten mounting bolts to 60 Nm now')...",
            key="engineer_response_input"
        )
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("💾 Submit Rule", type="primary"):
                if tacit_resp.strip():
                    resolve_result = orchestrator.resolve_conflict(
                        st.session_state['query_result'], 
                        choice='human', 
                        human_feedback=tacit_resp.strip()
                    )
                    st.session_state['conflict_resolution'] = 'human'
                    st.session_state['tacit_knowledge_saved'] = tacit_resp.strip()
                    st.session_state['resolution_details'] = resolve_result
                    st.session_state['query_result']['agent_log'].extend(resolve_result['agent_log'])
                    st.session_state['show_interview'] = False
                    st.success("Rule extracted successfully!")
                    st.rerun()
                else:
                    st.error("Please enter explanation details.")
        with col_btn2:
            if st.button("Cancel"):
                st.session_state['show_interview'] = False
                st.rerun()
