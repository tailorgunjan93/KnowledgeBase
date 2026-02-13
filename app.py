"""
Portable Knowledge Base System
A multi-user AI-powered knowledge base application with chat, summarization, and custom skills.
"""

import streamlit as st
from database.db_manager import DatabaseManager
from modules.auth import Auth
from modules.session import SessionManager
from modules.vector_store import VectorStore
from modules.knowledge_base import render_knowledge_base_page
from modules.chatbot import render_chat_page
from modules.summarizer import render_summarizer_page
from modules.skills_manager import render_skills_page
from modules.api_service import APIService
from utils.helpers import validate_email


# Page configuration
st.set_page_config(
    page_title="Knowledge Base System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize database and vector store
@st.cache_resource
def init_app():
    """Initialize application resources."""
    db = DatabaseManager()
    vector_store = VectorStore()
    auth = Auth(db)
    return db, vector_store, auth


db, vector_store, auth = init_app()

# Initialize session state
SessionManager.init_session_defaults()


def render_login_page():
    """Render login/signup page."""
    st.markdown('<div class="main-header">📚 Knowledge Base System</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-Powered Personal Knowledge Management</div>', unsafe_allow_html=True)
    
    # Tabs for login and signup
    tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if username and password:
                    user = auth.authenticate_user(username, password)
                    if user:
                        SessionManager.init_session(
                            user_id=user['id'],
                            username=user['username'],
                            email=user['email']
                        )
                        st.success(f"Welcome back, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter username and password")
    
    with tab2:
        st.markdown("### Create New Account")
        
        with st.form("signup_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
            
            if submit:
                if not new_username or not new_email or not new_password:
                    st.error("All fields are required")
                elif not validate_email(new_email):
                    st.error("Invalid email address")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    user_id = auth.create_user(new_username, new_email, new_password)
                    if user_id:
                        st.success("Account created! Please login.")
                    else:
                        st.error("Username or email already exists")
    
    # Features showcase
    st.markdown("---")
    st.markdown("## ✨ Features")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 📚 Knowledge Base")
        st.markdown("Upload and organize PDF, Excel, Word, and text files")
    
    with col2:
        st.markdown("### 💬 AI Chat")
        st.markdown("Chat with AI using your knowledge base with full conversation history")
    
    with col3:
        st.markdown("### 📝 Summarizer")
        st.markdown("Get AI-powered summaries of any document")
    
    with col4:
        st.markdown("### 🎯 Custom Skills")
        st.markdown("Create custom AI behaviors and response styles")


def render_settings_page():
    """Render settings page."""
    user_id = SessionManager.get_user_id()
    if not user_id:
        return
    
    st.title("⚙️ Settings")
    
    # API Key Configuration
    st.markdown("### 🔑 Groq API Configuration")
    st.markdown("""
    Get your free API key from [console.groq.com](https://console.groq.com)
    """)
    
    current_api_key = db.get_setting(user_id, 'groq_api_key')
    
    with st.form("api_key_form"):
        api_key = st.text_input(
            "Groq API Key",
            value=current_api_key if current_api_key else "",
            type="password"
        )
        
        col1, col2 = st.columns([1, 3])
        submit = col1.form_submit_button("Save", type="primary")
        test = col2.form_submit_button("Test Connection")
        
        if submit:
            if api_key:
                db.set_setting(user_id, 'groq_api_key', api_key)
                st.success("API key saved!")
                st.rerun()
            else:
                st.error("Please enter an API key")
        
        if test:
            if api_key:
                try:
                    api_service = APIService(api_key)
                    if api_service.validate_api_key():
                        st.success("✅ API key is valid!")
                    else:
                        st.error("❌ Invalid API key")
                except Exception as e:
                    st.error(f"❌ Error testing API key: {str(e)}")
            else:
                st.error("Please enter an API key first")
    
    # Model preferences
    st.markdown("---")
    st.markdown("### 🤖 Default Model")
    
    models = APIService.get_available_models()
    default_model = db.get_setting(user_id, 'default_model') or 'llama-3.1-70b-versatile'
    
    selected_model = st.selectbox(
        "Select default model",
        options=list(models.keys()),
        format_func=lambda x: models[x],
        index=list(models.keys()).index(default_model) if default_model in models else 0
    )
    
    if st.button("Save Model Preference"):
        db.set_setting(user_id, 'default_model', selected_model)
        st.success("Model preference saved!")
    
    # User info
    st.markdown("---")
    st.markdown("### 👤 Account Information")
    
    user = auth.get_user_by_id(user_id)
    if user:
        st.markdown(f"**Username:** {user['username']}")
        st.markdown(f"**Email:** {user['email']}")
        st.markdown(f"**Member since:** {user['created_at']}")


def render_main_app():
    """Render main application after login."""
    user = SessionManager.get_current_user()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"### Welcome, {user['username']}! 👋")
        st.markdown("---")
        
        # Navigation
        pages = {
            "📚 Knowledge Base": "Knowledge Base",
            "💬 Chat": "Chat",
            "📝 Summarizer": "Summarizer",
            "🎯 Skills": "Skills",
            "⚙️ Settings": "Settings"
        }
        
        for icon_label, page_name in pages.items():
            if st.button(icon_label, use_container_width=True, key=f"nav_{page_name}"):
                st.session_state.page = page_name
                st.rerun()
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            SessionManager.logout()
            st.rerun()
    
    # Main content area
    current_page = st.session_state.get('page', 'Knowledge Base')
    
    if current_page == "Knowledge Base":
        render_knowledge_base_page(db, vector_store)
    elif current_page == "Chat":
        render_chat_page(db, vector_store)
    elif current_page == "Summarizer":
        render_summarizer_page(db)
    elif current_page == "Skills":
        render_skills_page(db)
    elif current_page == "Settings":
        render_settings_page()


# Main app logic
def main():
    """Main application entry point."""
    if SessionManager.is_authenticated():
        render_main_app()
    else:
        render_login_page()


if __name__ == "__main__":
    main()
