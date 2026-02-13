"""Session management module."""
import streamlit as st
from typing import Optional, Dict


class SessionManager:
    """Manages user sessions using Streamlit session state."""
    
    @staticmethod
    def init_session(user_id: int, username: str, email: str):
        """
        Initialize user session after successful login.
        
        Args:
            user_id: User ID
            username: Username
            email: User email
        """
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.username = username
        st.session_state.email = email
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated."""
        return st.session_state.get('authenticated', False)
    
    @staticmethod
    def get_current_user() -> Optional[Dict]:
        """
        Get current logged-in user information.
        
        Returns:
            User dict with id, username, email if authenticated, None otherwise
        """
        if not SessionManager.is_authenticated():
            return None
        
        return {
            'id': st.session_state.get('user_id'),
            'username': st.session_state.get('username'),
            'email': st.session_state.get('email')
        }
    
    @staticmethod
    def get_user_id() -> Optional[int]:
        """Get current user ID."""
        return st.session_state.get('user_id')
    
    @staticmethod
    def logout():
        """Logout current user and clear session."""
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        
        # Clear other session state
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'user_id', 'username', 'email']:
                del st.session_state[key]
    
    @staticmethod
    def init_session_defaults():
        """Initialize default session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        
        if 'username' not in st.session_state:
            st.session_state.username = None
        
        if 'email' not in st.session_state:
            st.session_state.email = None
        
        if 'page' not in st.session_state:
            st.session_state.page = 'Knowledge Base'
        
        if 'selected_kb' not in st.session_state:
            st.session_state.selected_kb = None
        
        if 'selected_chat_session' not in st.session_state:
            st.session_state.selected_chat_session = None
