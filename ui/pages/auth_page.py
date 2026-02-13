"""Authentication Page with Premium UI."""
import streamlit as st
from domain.models import UserCreate
from data.repositories.user_repository import UserRepository
from core.security import SecurityManager
from ui.components import load_css

def render_auth_page():
    load_css()
    user_repo = UserRepository()
    
    # Theme Toggle Logic
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'

    def toggle_theme():
        st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

    # Inject Theme CSS based on session state
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
            :root {
                --bg-app: #0F172A !important;
                --bg-surface: #1E293B !important;
                --text-main: #F8FAFC !important;
                --text-secondary: #94A3B8 !important;
                --primary: #3B82F6 !important;
                --border-color: #334155 !important;
            }
            .stApp { background-color: var(--bg-app); }
            .auth-card { background-color: var(--bg-surface); border-color: var(--border-color); }
            h1, p { color: var(--text-main) !important; }
        </style>
        """, unsafe_allow_html=True)
        theme_icon = "☀️"
        theme_label = "Light Mode"
    else:
        theme_icon = "🌙"
        theme_label = "Dark Mode"
    
    # Header with toggle
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        if st.button(f"{theme_icon} {theme_label}", key="theme_toggle", help="Switch Theme"):
            toggle_theme()
            st.rerun()

    with col2:
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 2rem; padding-top: 2rem;'>
                <h1 style='color: var(--primary);'>🧠 Knowledge Base</h1>
                <p style='color: var(--text-secondary); font-size: 1.1rem;'>
                    Secure. Private. Intelligent.
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Use Native Streamlit container instead of custom HTML div for bounding box
        # This fixes the "empty white box" issue
        with st.container(border=True):
            tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up"])
            
            with tab1:
                st.write("") # Spacer
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    
                    st.write("") # Spacer
                    submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                    
                    if submitted:
                        if not username or not password:
                             st.error("Please enter both username and password.")
                        else:
                            user = user_repo.get_by_username(username)
                            if user and SecurityManager.verify_password(password, user.password_hash):
                                st.session_state['user_id'] = user.id
                                st.session_state['username'] = user.username
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error("Invalid credentials.")

            with tab2:
                st.write("")
                with st.form("signup_form"):
                    new_user = st.text_input("Username", placeholder="Choose a username")
                    email = st.text_input("Email", placeholder="name@example.com")
                    pwd = st.text_input("Password", type="password", placeholder="Min 6 characters")
                    confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                    
                    st.write("")
                    submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                    
                    if submitted:
                        if pwd != confirm:
                            st.error("Passwords do not match.")
                        elif len(pwd) < 6:
                            st.error("Password too short.")
                        elif user_repo.get_by_username(new_user):
                            st.error("Username already exists.")
                        else:
                            try:
                                hashed = SecurityManager.hash_password(pwd)
                                # Direct model creation as DTO mapping needs exact match
                                from domain.models import User
                                new_db_user = User(
                                    username=new_user, 
                                    email=email, 
                                    password_hash=hashed
                                )
                                user_repo.create(new_db_user)
                                st.success("Account created! Please log in.")
                            except Exception as e:
                                st.error(f"Error: {e}")
