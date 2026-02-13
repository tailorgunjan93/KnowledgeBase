"""Knowledge base management module."""
import streamlit as st
from typing import Optional, List, Dict
from database.db_manager import DatabaseManager
from modules.file_parser import FileParser
from modules.vector_store import VectorStore
from modules.session import SessionManager
from utils.helpers import format_timestamp, truncate_text
import requests
from bs4 import BeautifulSoup


def render_knowledge_base_page(db: DatabaseManager, vector_store: VectorStore):
    """
    Render the knowledge base management page.
    
    Args:
        db: Database manager instance
        vector_store: Vector store instance
    """
    user_id = SessionManager.get_user_id()
    if not user_id:
        st.error("Please log in to access knowledge bases")
        return
    
    st.title("📚 Knowledge Base")
    
    # Sidebar for KB selection and creation
    st.sidebar.markdown("### Your Knowledge Bases")
    
    # Create new KB button
    if st.sidebar.button("➕ Create New KB", use_container_width=True):
        st.session_state.show_create_kb = True
    
    # Get all KBs for user
    kbs = db.get_user_knowledge_bases(user_id)
    
    # Show create KB form
    if st.session_state.get('show_create_kb', False):
        with st.sidebar.expander("Create Knowledge Base", expanded=True):
            new_kb_name = st.text_input("Knowledge Base Name")
            col1, col2 = st.columns(2)
            if col1.button("Create"):
                if new_kb_name:
                    kb_id = db.create_knowledge_base(user_id, new_kb_name)
                    st.success(f"Created '{new_kb_name}'!")
                    st.session_state.show_create_kb = False
                    st.session_state.selected_kb = kb_id
                    st.rerun()
                else:
                    st.error("Please enter a name")
            if col2.button("Cancel"):
                st.session_state.show_create_kb = False
                st.rerun()
    
    # List existing KBs
    if kbs:
        st.sidebar.markdown("---")
        for kb in kbs:
            if st.sidebar.button(
                f"📁 {kb['name']}", 
                key=f"kb_{kb['id']}",
                use_container_width=True
            ):
                st.session_state.selected_kb = kb['id']
                st.rerun()
    else:
        st.sidebar.info("No knowledge bases yet. Create one to get started!")
    
    # Main content area
    if not st.session_state.get('selected_kb'):
        st.info("👈 Select or create a knowledge base to get started")
        
        # Show welcome message
        st.markdown("""
        ## Welcome to Knowledge Base Management
        
        Knowledge bases allow you to:
        - 📄 Upload and organize documents (PDF, Excel, Word, text files)
        - 🔗 Add content from URLs
        - 🔍 Search your documents semantically
        - 💬 Chat with AI about your documents
        
        **Get started** by creating a new knowledge base or selecting an existing one from the sidebar.
        """)
        return
    
    # Show selected KB
    kb_id = st.session_state.selected_kb
    kb = db.get_knowledge_base(kb_id, user_id)
    
    if not kb:
        st.error("Knowledge base not found")
        return
    
    # Header with KB name and actions
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"📁 {kb['name']}")
        st.caption(f"Created: {format_timestamp(kb['created_at'])}")
    
    with col2:
        if st.button("🗑️ Delete KB", type="secondary"):
            st.session_state.confirm_delete_kb = kb_id
    
    # Confirm delete
    if st.session_state.get('confirm_delete_kb') == kb_id:
        st.warning(f"⚠️ Delete '{kb['name']}'? This cannot be undone!")
        col1, col2, col3 = st.columns([1, 1, 2])
        if col1.button("Yes, Delete"):
            db.delete_knowledge_base(kb_id, user_id)
            vector_store.delete_kb_data(kb_id)
            st.session_state.selected_kb = None
            st.session_state.confirm_delete_kb = None
            st.success("Knowledge base deleted")
            st.rerun()
        if col2.button("Cancel"):
            st.session_state.confirm_delete_kb = None
            st.rerun()
    
    # Tabs for different actions
    tab1, tab2, tab3 = st.tabs(["📤 Upload Files", "🔗 Add from URL", "📋 View Documents"])
    
    # Tab 1: Upload files
    with tab1:
        st.markdown("### Upload Documents")
        st.markdown("Supported formats: PDF, Excel (.xlsx), Word (.docx), Text (.txt), CSV")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'xlsx', 'xls', 'docx', 'doc', 'txt', 'csv'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("Process Files", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"Processing {file.name}...")
                    try:
                        # Parse file
                        result = FileParser.parse_file(file, file.name)
                        
                        # Add to database
                        doc_id = db.add_document(
                            kb_id=kb_id,
                            user_id=user_id,
                            name=result['filename'],
                            content=result['content'],
                            file_type=result['file_type']
                        )
                        
                        # Add to vector store
                        vector_store.add_document(
                            kb_id=kb_id,
                            text=result['content'],
                            metadata={
                                'doc_id': doc_id,
                                'name': result['filename'],
                                'file_type': result['file_type']
                            }
                        )
                        
                        st.success(f"✅ {file.name}")
                    except Exception as e:
                        st.error(f"❌ {file.name}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("Done!")
                st.rerun()
    
    # Tab 2: Add from URL
    with tab2:
        st.markdown("### Add Content from URL")
        st.markdown("Paste a URL to extract and add its text content to your knowledge base")
        
        url = st.text_input("Enter URL")
        
        if st.button("Fetch and Add", type="primary"):
            if url:
                try:
                    with st.spinner("Fetching content..."):
                        # Fetch URL
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        
                        # Parse HTML
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text
                        text = soup.get_text()
                        
                        # Clean text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = '\n'.join(chunk for chunk in chunks if chunk)
                        
                        if not text:
                            st.error("No text content found at URL")
                        else:
                            # Add to database
                            doc_id = db.add_document(
                                kb_id=kb_id,
                                user_id=user_id,
                                name=url,
                                content=text,
                                file_type='url'
                            )
                            
                            # Add to vector store
                            vector_store.add_document(
                                kb_id=kb_id,
                                text=text,
                                metadata={
                                    'doc_id': doc_id,
                                    'name': url,
                                    'file_type': 'url'
                                }
                            )
                            
                            st.success(f"✅ Added content from {url}")
                            st.rerun()
                
                except Exception as e:
                    st.error(f"Error fetching URL: {str(e)}")
            else:
                st.warning("Please enter a URL")
    
    # Tab 3: View documents
    with tab3:
        st.markdown("### Documents in this Knowledge Base")
        
        docs = db.get_kb_documents(kb_id, user_id)
        
        if not docs:
            st.info("No documents yet. Upload files or add content from URLs to get started!")
        else:
            st.markdown(f"**Total documents:** {len(docs)}")
            
            # Search box
            search_query = st.text_input("🔍 Search documents", placeholder="Enter search query...")
            
            if search_query:
                # Semantic search
                results = vector_store.search(kb_id, search_query, top_k=10)
                
                if results:
                    st.markdown(f"**Found {len(results)} relevant chunks:**")
                    for result in results:
                        with st.expander(f"📄 {result['metadata']['name']} (Relevance: {result['score']:.2%})"):
                            st.markdown(f"**Chunk {result['chunk_index'] + 1}**")
                            st.markdown(result['text'])
                else:
                    st.info("No matching results found")
            else:
                # List all documents
                for doc in docs:
                    with st.expander(f"📄 {doc['name']} ({doc['file_type']})"):
                        st.caption(f"Added: {format_timestamp(doc['created_at'])}")
                        st.markdown("**Content preview:**")
                        st.text(truncate_text(doc['content'], 500))
                        
                        if st.button(f"Delete", key=f"del_doc_{doc['id']}"):
                            db.delete_document(doc['id'], user_id)
                            st.success("Document deleted")
                            st.rerun()
