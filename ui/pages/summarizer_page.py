"""Summarizer Page."""
import streamlit as st
from services.summarizer_service import SummarizerService
from services.file_processing.parser import FileParserService
from ui.components import load_css

def render_summarizer_page():
    load_css()
    summarizer = SummarizerService()
    parser = FileParserService()
    
    st.markdown("## 📝 Document Summarizer")
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.warning("Please log in.")
        st.stop()
        
    c1, c2 = st.columns([1, 1])
    with c1:
        length = st.select_slider("Length", options=["short", "medium", "long"], value="medium")
    with c2:
        style = st.selectbox("Style", ["bullet_points", "paragraph", "executive"])

    uploaded_file = st.file_uploader("Upload Document (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])
    
    if uploaded_file and st.button("Generate Summary", type="primary"):
        with st.spinner("Reading & Summarizing..."):
            try:
                # 1. Parse
                text = parser.parse_file(uploaded_file, uploaded_file.name)
                
                # 2. Summarize
                summary = summarizer.generate_summary(text, length, style, user_id)
                
                # 3. Display
                st.markdown("### Summary Result")
                st.markdown(f'<div class="doc-card" style="line-height:1.6;">{summary}</div>', unsafe_allow_html=True)
                st.download_button("Download Summary", summary, file_name="summary.txt")
                
            except Exception as e:
                st.error(f"Error: {e}")
