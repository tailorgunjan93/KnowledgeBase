"""Main Application Entry Point (Refactored & Complete)."""
import streamlit as st
from ui.pages.auth_page import render_auth_page
from ui.pages.kb_page import render_kb_page
from ui.pages.chat_page import render_chat_page
from ui.pages.summarizer_page import render_summarizer_page
from ui.pages.skills_page import render_skills_page
from ui.pages.settings_page import render_settings_page
from core.config import settings

st.set_page_config(
    page_title=settings.APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Session State Initialization
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None

    # Routing Logic
    if not st.session_state['user_id']:
        render_auth_page()
    else:
        # Authenticated Layout
        with st.sidebar:
            st.markdown(f"**👤 {st.session_state.get('username', 'User')}**")
            
            # Page Routing
            if 'current_page' not in st.session_state:
                st.session_state['current_page'] = "Chat"

            # Nav Buttons
            if st.button("💬 Chat", use_container_width=True): st.session_state['current_page'] = "Chat"
            if st.button("📚 Knowledge Base", use_container_width=True): st.session_state['current_page'] = "Knowledge Base"
            if st.button("📝 Summarizer", use_container_width=True): st.session_state['current_page'] = "Summarizer"
            if st.button("🎭 Skills", use_container_width=True): st.session_state['current_page'] = "Skills"
            if st.button("⚙️ Settings", use_container_width=True): st.session_state['current_page'] = "Settings"

            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state['user_id'] = None
                st.session_state['current_page'] = "Chat"
                st.rerun()
        
        # Render Selection
        page = st.session_state.get('current_page', "Chat")
        
        if page == "Knowledge Base":
            render_kb_page()
        elif page == "Summarizer":
            render_summarizer_page()
        elif page == "Chat":
            render_chat_page()
        elif page == "Skills":
            render_skills_page()
        elif page == "Settings":
            render_settings_page()

if __name__ == "__main__":
    main()
