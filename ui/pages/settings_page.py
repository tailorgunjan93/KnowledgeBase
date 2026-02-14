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
    current_model = repo.get_value(user_id, "default_model") or "llama-3.3-70b-versatile"
    
    # Get available models
    available_models = APIService.get_available_models()
    model_options = list(available_models.keys()) + ["Custom"]
    
    # Determine index
    if current_model in available_models:
        index = model_options.index(current_model)
        is_custom = False
    else:
        index = model_options.index("Custom")
        is_custom = True
    
    selected_option = st.selectbox(
        "Select Model", 
        model_options, 
        format_func=lambda x: available_models.get(x, x),
        index=index
    )
    
    final_model = selected_option
    
    if selected_option == "Custom" or is_custom:
        # If custom was already selected (saved), pre-fill the input
        default_custom = current_model if is_custom else ""
        custom_model = st.text_input("Enter Custom Model ID", value=default_custom, help="e.g., llama3-70b-8192")
        if custom_model:
            final_model = custom_model
    
    if st.button("💾 Save Model Preference"):
        if final_model == "Custom" and not custom_model:
            st.error("Please enter a custom model ID")
        else:
            repo.set_value(user_id, "default_model", final_model)
            st.success(f"Preference Saved! Using: {final_model}")
            # Rerun to update state
            st.rerun()

    # 3. System Info
    st.markdown("---")
    st.caption(f"User ID: {user_id}")
