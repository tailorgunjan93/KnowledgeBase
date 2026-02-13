"""Chat Interface with Responsive Design."""
import streamlit as st
import time
from services.chat_service import ChatService
from data.repositories.kb_repository import KbRepository
from domain.models import ChatSession
from ui.components import load_css, chat_message_bubble

def render_chat_page():
    load_css()
    chat_service = ChatService()
    kb_repo = KbRepository()
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.warning("Please log in to chat.")
        st.stop()

    # --- Header ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("## 💬 AI Assistant")
    with c2:
        # Context Selector in Header for better visibility
        kbs = kb_repo.get_user_kbs(user_id)
        kb_options = {0: "🧠 General Knowledge"}
        kb_options.update({kb.id: f"📚 {kb.name}" for kb in kbs})
        
        selected_kb = st.selectbox(
            "Context",
            options=kb_options.keys(),
            format_func=lambda x: kb_options[x],
            index=0,
            label_visibility="collapsed"
        )
        kb_id = selected_kb if selected_kb != 0 else None

    # --- Sidebar (Sessions) ---
    sessions = chat_service.chat_repo.get_user_sessions(user_id)
    
    with st.sidebar:
        st.markdown("### 🗂️ Interactions")
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            session_model = ChatSession(user_id=user_id)
            new_id = chat_service.chat_repo.create(session_model)
            st.session_state['active_session_id'] = new_id
            st.rerun()
            
        # Skill Selection Sidebar
        from data.repositories.settings_repository import SkillRepository
        skill_repo = SkillRepository()
        skills = skill_repo.get_user_skills(user_id)
        skill_options = {0: "🤖 Default Assistant"}
        skill_options.update({s.id: f"🎭 {s.name}" for s in skills})
        
        selected_skill = st.selectbox(
            "Persona / Skill",
            options=skill_options.keys(),
            format_func=lambda x: skill_options[x]
        )
        skill_id = selected_skill if selected_skill != 0 else None
            
        st.markdown("---")
        st.markdown("<div style='max-height: 50vh; overflow-y: auto;'>", unsafe_allow_html=True)
        for s in sessions[:15]:
            # Highlight active session
            active = st.session_state.get('active_session_id') == s.id
            label = f"{'🔹' if active else '🗨️'} {s.title[:22]}..."
            if st.button(label, key=f"sess_{s.id}", use_container_width=True):
                st.session_state['active_session_id'] = s.id
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
                
    # --- Active Session Logic ---
    session_id = st.session_state.get('active_session_id')
    if not session_id and sessions:
        session_id = sessions[0].id
        st.session_state['active_session_id'] = session_id
    elif not session_id:
        session_model = ChatSession(user_id=user_id)
        new_id = chat_service.chat_repo.create(session_model)
        st.session_state['active_session_id'] = new_id
        session_id = new_id

    # --- Chat Area ---
    # Use a container for messages to separate from input
    chat_container = st.container()
    
    with chat_container:
        messages = chat_service.msg_repo.get_session_messages(session_id)
        
        if not messages:
            st.markdown(
                """
                <div style='text-align: center; color: var(--text-secondary); padding: 4rem 2rem;'>
                    <h3>👋 Ready to help!</h3>
                    <p>Select a Knowledge Base from the top right to chat with your documents, 
                    or just ask me anything.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            for msg in messages:
                chat_message_bubble(msg.role, msg.content)
            
            # Spacer for bottom input
            st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

    # --- Input Area (Fixed Bottom) ---
    if prompt := st.chat_input("Type your message here..."):
        # Add User Message to History immediately
        with chat_container:
            chat_message_bubble("user", prompt)
            
        # Stream Response
        with chat_container:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_response = ""
                
                try:
                    stream = chat_service.process_message(
                        user_id=user_id,
                        session_id=session_id,
                        content=prompt,
                        kb_id=kb_id,
                        skill_id=skill_id
                    )
                    for chunk in stream:
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    
        # Force rerun to update history in sidebar/state correctly if needed
        # But for streaming, usually we let it stay. 
        # If title updates are implemented, we might want a rerun eventually.
