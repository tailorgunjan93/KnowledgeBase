"""Reusable UI components."""
import streamlit as st


def load_css():
    """Load the main CSS file."""
    with open("ui/styles/main.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def chat_message_bubble(role: str, content: str, avatar: str = None):
    """
    Render a styled chat message bubble.
    
    Args:
        role: "user" or "assistant"
        content: Message content (markdown supported)
        avatar: Optional emoji or image URL
    """
    # Use standard Streamlit chat message for better compatibility but inject custom classes
    with st.chat_message(role, avatar=avatar):
        st.markdown(f'<div class="chat-message {role}">', unsafe_allow_html=True)
        st.markdown(content)
        st.markdown('</div>', unsafe_allow_html=True)


def document_card(title: str, meta: str, on_delete=None, key=None):
    """
    Render a card for a document in the Knowledge Base list.
    """
    cols = st.columns([4, 1])
    with cols[0]:
        st.markdown(f"""
        <div class="doc-card">
            <div style="font-weight: 600;">📄 {title}</div>
            <div style="font-size: 0.8rem; color: #666;">{meta}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        if on_delete:
            if st.button("🗑️", key=key, help="Delete Document"):
                on_delete()


def status_badge(text: str, type: str = "success"):
    """Render a colored status badge."""
    st.markdown(f'<span class="status-badge status-{type}">{text}</span>', unsafe_allow_html=True)
