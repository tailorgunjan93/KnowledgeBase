"""Settings Page for User Preferences."""
import streamlit as st
from data.repositories.settings_repository import SettingsRepository
from services.api_service import APIService
from ui.components import load_css

def render_settings_page():
    load_css()
    repo = SettingsRepository()
    user_id = st.session_state.get('user_id')
    
    if not user_id:
        st.warning("Login required.")
        return
        
    st.markdown("## ⚙️ Settings")
    
    # 1. API Configuration
    st.markdown("### 🔑 API Configuration")
    current_key = repo.get_value(user_id, "groq_api_key")
    
    with st.form("api_settings"):
        api_key = st.text_input("Groq API Key", value=current_key if current_key else "", type="password")
        if st.form_submit_button("Save Key", type="primary"):
            repo.set_value(user_id, "groq_api_key", api_key)
            st.success("API Key Saved!")
            st.rerun()

    # 2. Model Preference
    st.markdown("### 🤖 Model Preference")
    current_model = repo.get_value(user_id, "default_model") or "llama-3.1-70b-versatile"
    
    model_options = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]
    
    selected = st.selectbox("Default Model", model_options, index=model_options.index(current_model) if current_model in model_options else 0)
    
    if st.button("Update Model Preference"):
        repo.set_value(user_id, "default_model", selected)
        st.success("Preference Saved!")

    # 3. System Info
    st.markdown("---")
    st.caption(f"User ID: {user_id}")
