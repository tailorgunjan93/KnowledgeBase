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
    
    # Status Indicator
    if current_key:
        st.success(f"✅ API Key is saved (ends in ...{current_key[-4:]})")
    else:
        st.warning("⚠️ No API Key configured. Chat features will not work.")

    with st.form("api_settings"):
        new_key = st.text_input("Update API Key", type="password", help="Enter your Groq API Key")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            save = st.form_submit_button("💾 Save Key", type="primary", use_container_width=True)
        with c2:
            test = st.form_submit_button("🔌 Test Connection", use_container_width=True)

        if save:
            if new_key:
                repo.set_value(user_id, "groq_api_key", new_key)
                st.success("API Key Saved!")
                st.rerun()
            else:
                st.error("Please enter a key to save.")
        
        if test:
            key_to_test = new_key if new_key else current_key
            if not key_to_test:
                st.error("No key to test. Please save one or enter it.")
            else:
                api = APIService(key_to_test)
                if api.validate_api_key():
                    st.success("✅ Connection Successful!")
                else:
                    st.error("❌ Connection Failed. Check your key.")

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
