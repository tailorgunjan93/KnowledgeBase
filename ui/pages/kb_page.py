"""Knowledge Base Management with Premium UI."""
import streamlit as st
import pandas as pd
from datetime import datetime
from services.file_processing.parser import FileParserService
from services.vector_service import VectorService
from data.repositories.kb_repository import KbRepository, DocumentRepository
from domain.models import Document, KnowledgeBase
from ui.components import load_css, status_badge
from core.config import settings
from domain.exceptions import ValidationError

def render_kb_page():
    load_css()
    
    # Initialize services & repositories
    parser_service = FileParserService()
    vector_service = VectorService()
    kb_repo = KbRepository()
    doc_repo = DocumentRepository()
    
    # Header
    st.markdown("## 📚 Knowledge Base Manager")
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.warning("Please log in to manage your knowledge base.")
        st.stop()

    # --- Sidebar: KB Selection & Creation ---
    kbs = kb_repo.get_user_kbs(user_id)
    kb_options = {kb.id: kb.name for kb in kbs}
    
    selected_kb_id = st.sidebar.selectbox(
        "Current Knowledge Base",
        options=kb_options.keys(),
        format_func=lambda x: kb_options[x]
    )
    
    with st.sidebar.expander("➕ Create New Knowledge Base"):
        with st.form("create_kb_form"):
            new_kb_name = st.text_input("Name", placeholder="e.g. Finance Docs")
            if st.form_submit_button("Create", type="primary"):
                if new_kb_name:
                    kb = KnowledgeBase(user_id=user_id, name=new_kb_name)
                    kb_repo.create(kb)
                    st.success("Created!")
                    st.rerun()

    if not selected_kb_id:
        st.info("👈 Create or Select a Knowledge Base to start.")
        return

    # --- Main Content Area ---
    st.markdown(f"### Manage: {kb_options[selected_kb_id]}")
    
    # Use tabs for separation of concerns
    tab_upload, tab_view = st.tabs(["📤 Upload Documents", "📄 View Content"])
    
    # Tab 1: Upload (Card Style)
    with tab_upload:
        st.markdown('<div class="doc-card" style="display:block;">', unsafe_allow_html=True)
        st.markdown("#### Upload Files")
        st.caption("Supported formats: PDF, DOCX, TXT, CSV, Excel")
        
        uploaded_files = st.file_uploader(
            "Drag and drop files here",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if st.button("Process & Index Files", type="primary", use_container_width=True):
            if not uploaded_files:
                st.warning("No files selected.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"Processing {file.name}...")
                    try:
                        # 1. Parse File
                        content = parser_service.parse_file(file, file.name)
                        
                        # 2. Save Document Record
                        doc_model = Document(
                            kb_id=selected_kb_id,
                            user_id=user_id,
                            name=file.name,
                            content=content,
                            file_type=file.name.split('.')[-1]
                        )
                        doc_id = doc_repo.create(doc_model)
                        doc_model.id = doc_id 
                        
                        # 3. Vector Embeddings
                        vector_service.add_document(selected_kb_id, doc_model)
                        
                    except ValidationError as e:
                        st.error(f"Validation Error ({file.name}): {str(e)}")
                    except Exception as e:
                        st.error(f"Error ({file.name}): {str(e)}")
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("Done!")
                st.success(f"Successfully processed {len(uploaded_files)} files!")
                time.sleep(1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Tab 2: View Documents (Grid/List)
    with tab_view:
        documents = doc_repo.get_kb_documents(selected_kb_id)
        if not documents:
            st.info("No documents found in this Knowledge Base.")
        else:
            st.markdown(f"**Total Documents:** {len(documents)}")
            for doc in documents:
                # Custom Card Component for Document
                col_text, col_act = st.columns([5, 1])
                with col_text:
                    st.markdown(f"""
                    <div class="doc-card">
                        <div>
                            <div style="font-weight:600; font-size:1rem;">📄 {doc.name}</div>
                            <div style="font-size:0.8rem; color: #666;">
                                Added: {doc.created_at.strftime('%Y-%m-%d %H:%M')} • Size: {len(doc.content)} chars
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_act:
                    if st.button("🗑️", key=f"del_{doc.id}", help="Delete"):
                        doc_repo.delete(doc.id)
                        # TODO: Remove from vector store in future
                        st.rerun()
                        
                with st.expander("View Content Preview"):
                    st.text(doc.content[:500] + "...")
