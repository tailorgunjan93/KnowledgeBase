# Portable Knowledge Base System

A multi-user knowledge base system built with Python and Streamlit, featuring AI-powered chat, document processing, and custom skills.

## Features

- 🔐 **Multi-User Authentication**: Secure signup/login with bcrypt password hashing
- 📚 **Knowledge Base Management**: Upload and organize PDF, Excel, Word, and text files
- 💬 **AI Chat with History**: ChatGPT-style interface with multiple sessions and conversation history
- 🔍 **Semantic Search**: FAISS-powered vector search for relevant document retrieval
- 📝 **Document Summarization**: AI-powered summarization with customizable styles
- 🎯 **Custom Skills**: Create and apply custom AI behaviors and output formats
- 🚀 **Open-Source Models**: Powered by Groq API (Llama 3, Mixtral, Gemma)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Get your Groq API key**:
   - Visit [console.groq.com](https://console.groq.com)
   - Sign up for a free account
   - Generate an API key

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### First Time Setup

1. **Sign Up**: Create an account with a username, email, and password
2. **Login**: Use your credentials to access the application
3. **Configure API Key**: Go to Settings and enter your Groq API key
4. **Create Knowledge Base**: Start adding documents to your personal knowledge base

### Features Guide

#### Knowledge Base
- Click "Knowledge Base" in the sidebar
- Create a new knowledge base or select an existing one
- Upload PDF, Excel, Word, or text files
- Add content from URLs by pasting the URL
- View and search your documents

#### Chat
- Click "Chat" in the sidebar
- Select a knowledge base to chat about
- Click "+ New Chat" to start a new conversation
- Ask questions - the AI will use your knowledge base to answer
- Switch between different chat sessions in the sidebar
- The AI remembers the full conversation history in each session

#### Summarizer
- Click "Summarizer" in the sidebar
- Upload any document
- Choose summary style (bullet points, paragraph, etc.)
- Adjust summary length
- Get instant AI-powered summary

#### Skills
- Click "Skills" in the sidebar
- Create custom skills to control AI output format
- Choose from predefined templates (Technical, Creative, Formal, etc.)
- Apply skills to your chat conversations
- Edit or delete skills as needed

#### Settings
- Click "Settings" in the sidebar
- Configure your Groq API key
- Select preferred AI model (Llama 3, Mixtral, or Gemma)
- Update your profile information

## Architecture

- **Frontend**: Streamlit (Python)
- **Database**: SQLite (with user data isolation)
- **AI**: Groq API with open-source models
- **Vector Search**: FAISS + sentence-transformers
- **Authentication**: bcrypt password hashing

## Data Privacy

- Each user's data is completely isolated
- All knowledge bases, chat sessions, and skills are private to each user
- API keys are stored encrypted per user
- Passwords are hashed using bcrypt

## Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

### API errors
- Verify your Groq API key is correct in Settings
- Check your internet connection
- Ensure you haven't exceeded API rate limits

### File upload issues
- Supported formats: PDF, Excel (.xlsx), Word (.docx), plain text
- Maximum recommended file size: 10MB for PDFs, 5MB for Excel
- Ensure files are not corrupted

### Chat not responding
- Make sure you've configured your API key in Settings
- Select a knowledge base before chatting
- Check that the knowledge base contains documents

## License

This project is open source and available for personal and educational use.

## Support

For issues or questions, please refer to the troubleshooting section above or check the Groq API documentation at [console.groq.com/docs](https://console.groq.com/docs).
