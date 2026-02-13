"""Chatbot module with session management and history-aware conversations."""
import streamlit as st
from typing import List, Dict, Optional
from database.db_manager import DatabaseManager
from modules.api_service import APIService
from modules.vector_store import VectorStore
from modules.session import SessionManager
from utils.helpers import format_timestamp, truncate_text


def render_chat_page(db: DatabaseManager, vector_store: VectorStore):
    """
    Render the chat interface with session management.
    
    Args:
        db: Database manager instance
        vector_store: Vector store instance
    """
    user_id = SessionManager.get_user_id()
    if not user_id:
        st.error("Please log in to use chat")
        return
    
    st.title("💬 AI Chat")
    
    # Check API key
    api_key = db.get_setting(user_id, 'groq_api_key')
    if not api_key:
        st.warning("⚠️ Please configure your Groq API key in Settings to use chat")
        return
    
    # Get knowledge bases
    kbs = db.get_user_knowledge_bases(user_id)
    
    # Sidebar for chat sessions
    st.sidebar.markdown("### Chat Sessions")
    
    # New chat button
    if st.sidebar.button("➕ New Chat", use_container_width=True, type="primary"):
        # Create new chat session
        session_id = db.create_chat_session(
            user_id=user_id,
            kb_id=st.session_state.get('chat_kb_id'),
            title="New Chat"
        )
        st.session_state.selected_chat_session = session_id
        st.rerun()
    
    # List existing chat sessions
    chat_sessions = db.get_user_chat_sessions(user_id)
    
    if chat_sessions:
        st.sidebar.markdown("---")
        for session in chat_sessions[:20]:  # Show last 20 sessions
            # Truncate title for display
            display_title = truncate_text(session['title'], 30)
            
            # Show when it was last updated
            time_str = format_timestamp(session['updated_at'])
            
            if st.sidebar.button(
                f"💬 {display_title}",
                key=f"session_{session['id']}",
                use_container_width=True,
                help=f"Last updated: {time_str}"
            ):
                st.session_state.selected_chat_session = session['id']
                st.rerun()
    
    # Main chat area
    if not st.session_state.get('selected_chat_session'):
        st.info("👈 Start a new chat or select an existing conversation")
        
        st.markdown("""
        ## 🤖 AI Chat Assistant        **What can I help you with today?**
        
        The AI can:
        - 💬 Have natural conversations with full history awareness
        - 📚 Answer questions from your knowledge bases
        - 🎯 Apply custom skills to modify response style
        - 🔍 Use semantic search to find relevant information
        
        **Get started** by clicking "New Chat" or selecting a previous conversation.
        """)
        return
    
    # Get current session
    session_id = st.session_state.selected_chat_session
    session = db.get_chat_session(session_id, user_id)
    
    if not session:
        st.error("Chat session not found")
        st.session_state.selected_chat_session = None
        return
    
    # Top bar with session info and options
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.subheader(f"💬 {session['title']}")
    
    with col2:
        # Knowledge base selector
        kb_options = {0: "No KB"} | {kb['id']: kb['name'] for kb in kbs}
        current_kb = session['kb_id'] if session['kb_id'] else 0
        
        selected_kb = st.selectbox(
            "Knowledge Base",
            options=list(kb_options.keys()),
            format_func=lambda x: kb_options[x],
            index=list(kb_options.keys()).index(current_kb),
            key=f"kb_select_{session_id}"
        )
        
        if selected_kb != current_kb:
            st.session_state.chat_kb_id = selected_kb if selected_kb != 0 else None
    
    with col3:
        # Delete session button
        if st.button("🗑️ Delete", key=f"del_session_{session_id}"):
            if db.delete_chat_session(session_id, user_id):
                st.session_state.selected_chat_session = None
                st.success("Chat deleted")
                st.rerun()
    
    # Get skills for selection
    skills = db.get_user_skills(user_id)
    
    # Skill selector (optional)
    with st.expander("⚙️ Chat Settings"):
        # Model selection
        models = APIService.get_available_models()
        selected_model = st.selectbox(
            "Model",
            options=list(models.keys()),
            format_func=lambda x: models[x],
            index=0
        )
        
        # Skill selection
        skill_options = {0: "No Skill"} | {s['id']: s['name'] for s in skills}
        selected_skill_id = st.selectbox(
            "Apply Skill",
            options=list(skill_options.keys()),
            format_func=lambda x: skill_options[x]
        )
        
        selected_skill = None
        if selected_skill_id != 0:
            selected_skill = db.get_skill(selected_skill_id, user_id)
    
    # Display chat history
    messages = db.get_chat_messages(session_id)
    
    # Container for chat messages
    chat_container = st.container()
    
    with chat_container:
        for msg in messages:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to display
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # Save user message
        db.add_chat_message(session_id, "user", prompt)
        
        # Update title if first message
        if len(messages) == 0:
            title = truncate_text(prompt, 50)
            # Update session title in database
            db.get_connection().execute(
                "UPDATE chat_sessions SET title = ? WHERE id = ?",
                (title, session_id)
            )
            db.get_connection().commit()
            db.get_connection().close()
        
        # Get context from knowledge base if selected
        context_text = ""
        if st.session_state.get('chat_kb_id'):
            kb_id = st.session_state.chat_kb_id
            # Search for relevant documents
            results = vector_store.search(kb_id, prompt, top_k=3)
            
            if results:
                context_text = "\n\n".join([
                    f"[From {r['metadata']['name']}]: {r['text']}"
                    for r in results
                ])
        
        # Build message history for API
        api_messages = []
        
        # Add system message with context if available
        if context_text:
            system_msg = f"""You are a helpful AI assistant. Use the following context from the user's knowledge base to answer their question:

{context_text}

If the context doesn't contain relevant information, you can still answer based on your general knowledge, but mention that you're not finding specific information in their knowledge base."""
            api_messages.append({"role": "system", "content": system_msg})
        else:
            api_messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."
            })
        
        # Add conversation history
        for msg in messages:
            api_messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Add current prompt
        api_messages.append({"role": "user", "content": prompt})
        
        # Apply skill if selected
        if selected_skill:
            # Modify the system message or add instruction
            skill_instruction = f"\n\nIMPORTANT: {selected_skill['prompt_template']}"
            api_messages[0]['content'] += skill_instruction
        
        # Get AI response with streaming
        try:
            api_service = APIService(api_key)
            
            # Display assistant response with streaming
            with chat_container:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    for chunk in api_service.chat_completion_stream(
                        messages=api_messages,
                        model=selected_model,
                        temperature=0.7
                    ):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
            
            # Save assistant message
            db.add_chat_message(session_id, "assistant", full_response)
            
            # Rerun to show updated history
            st.rerun()
        
        except Exception as e:
            st.error(f"Error getting AI response: {str(e)}")
