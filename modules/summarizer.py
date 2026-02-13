"""Document summarization module."""
import streamlit as st
from database.db_manager import DatabaseManager
from modules.api_service import APIService
from modules.file_parser import FileParser
from modules.session import SessionManager


def render_summarizer_page(db: DatabaseManager):
    """
    Render the document summarizer page.
    
    Args:
        db: Database manager instance
    """
    user_id = SessionManager.get_user_id()
    if not user_id:
        st.error("Please log in to use summarizer")
        return
    
    st.title("📝 Document Summarizer")
    
    # Check API key
    api_key = db.get_setting(user_id, 'groq_api_key')
    if not api_key:
        st.warning("⚠️ Please configure your Groq API key in Settings to use the summarizer")
        return
    
    st.markdown("""
    Upload a document and get an AI-powered summary instantly.
    
    **Supported formats:** PDF, Excel, Word, text files, CSV
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file to summarize",
        type=['pdf', 'xlsx', 'xls', 'docx', 'doc', 'txt', 'csv']
    )
    
    if uploaded_file:
        # Summary options
        col1, col2 = st.columns(2)
        
        with col1:
            summary_length = st.select_slider(
                "Summary Length",
                options=["Very Short", "Short", "Medium", "Long", "Detailed"],
                value="Medium"
            )
        
        with col2:
            summary_style = st.selectbox(
                "Summary Style",
                options=[
                    "Bullet Points",
                    "Paragraph",
                    "Key Takeaways",
                    "Executive Summary",
                    "Technical Summary"
                ]
            )
        
        # Model selection
        models = APIService.get_available_models()
        selected_model = st.selectbox(
            "Model",
            options=list(models.keys()),
            format_func=lambda x: models[x],
            index=0
        )
        
        if st.button("✨ Generate Summary", type="primary"):
            try:
                # Parse the file
                with st.spinner("Extracting text from file..."):
                    result = FileParser.parse_file(uploaded_file, uploaded_file.name)
                    text = result['content']
                
                # Check text length
                st.info(f"📄 Extracted {len(text)} characters from {uploaded_file.name}")
                
                # Build summary prompt
                length_instructions = {
                    "Very Short": "in 2-3 sentences",
                    "Short": "in about 100 words",
                    "Medium": "in about 250 words",
                    "Long": "in about 500 words",
                    "Detailed": "comprehensively, covering all key points"
                }
                
                style_instructions = {
                    "Bullet Points": "Format as clear bullet points.",
                    "Paragraph": "Write in paragraph form.",
                    "Key Takeaways": "Focus on the main takeaways and insights.",
                    "Executive Summary": "Write as an executive summary for business purposes.",
                    "Technical Summary": "Provide a technical summary with specific details."
                }
                
                prompt = f"""Summarize the following document {length_instructions[summary_length]}. 
{style_instructions[summary_style]}

Document content:
{text[:10000]}""" # Limit to 10k chars for API
                
                # Get summary from API
                with st.spinner("Generating summary..."):
                    api_service = APIService(api_key)
                    
                    messages = [
                        {"role": "system", "content": "You are an expert at summarizing documents clearly and concisely."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    summary = api_service.chat_completion(
                        messages=messages,
                        model=selected_model,
                        temperature=0.3
                    )
                
                # Display summary
                st.markdown("---")
                st.markdown("### 📋 Summary")
                st.markdown(summary)
                
                # Download button
                st.download_button(
                    label="⬇️ Download Summary",
                    data=summary,
                    file_name=f"{uploaded_file.name}_summary.txt",
                    mime="text/plain"
                )
            
            except Exception as e:
                st.error(f"Error generating summary: {str(e)}")
