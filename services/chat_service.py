"""Chat service for handling conversation flow."""
from typing import List, Dict, Optional, Generator
from groq import Groq
from domain.models import ChatSession, ChatMessage
from data.repositories.chat_repository import ChatRepository, MessageRepository
from data.repositories.settings_repository import SettingsRepository, SkillRepository
from services.vector_service import VectorService
from core.config import settings
from domain.exceptions import ValidationError, ExternalServiceError


class ChatService:
    """
    Orchestrates the chat experience:
    - Context retrieval
    - Prompt assembly
    - LLM interaction
    - History persistence
    """
    
    def __init__(self):
        self.chat_repo = ChatRepository()
        self.msg_repo = MessageRepository()
        self.settings_repo = SettingsRepository()
        self.skill_repo = SkillRepository()
        self.vector_service = VectorService()

    def _get_api_client(self, user_id: int) -> Groq:
        """Get Groq client with user's API key."""
        api_key = self.settings_repo.get_value(user_id, 'groq_api_key')
        if not api_key:
            # Fallback to env var for dev/testing
            api_key = settings.GROQ_API_KEY
            
        if not api_key:
            raise ValidationError("Groq API Key not found. Please configure it in settings.")
            
        return Groq(api_key=api_key)

    def process_message(
        self, 
        user_id: int, 
        session_id: int, 
        content: str, 
        kb_id: Optional[int] = None,
        skill_id: Optional[int] = None,
        model: str = "llama-3.1-70b-versatile"
    ) -> Generator[str, None, None]:
        """
        Process a user message: save it, retrieve context, stream response, save response.
        """
        # 1. Save User Message
        user_msg = ChatMessage(session_id=session_id, role='user', content=content)
        self.msg_repo.create(user_msg)
        
        # 2. Retrieve Context (if KB selected)
        context = ""
        if kb_id:
            results = self.vector_service.search(kb_id, content, limit=3)
            if results:
                context = "\n\n".join([f"Source: {r['source']}\n{r['text']}" for r in results])
        
        # 3. Retrieve Skill (if selected)
        skill_instruction = ""
        if skill_id:
            skill = self.skill_repo.get_by_id(skill_id)
            if skill:
                skill_instruction = f"\n\nIMPORTANT INSTRUCTION: {skill.prompt_template}"

        # 4. Build System Prompt and History
        messages = self._build_messages(session_id, content, context, skill_instruction)
        
        # 5. Stream Response from LLM
        client = self._get_api_client(user_id)
        full_response = ""
        
        try:
            stream = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=0.7,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text_chunk = chunk.choices[0].delta.content
                    full_response += text_chunk
                    yield text_chunk
                    
        except Exception as e:
            raise ExternalServiceError(f"LLM Error: {str(e)}")
            
        # 6. Save Assistant Response
        asst_msg = ChatMessage(session_id=session_id, role='assistant', content=full_response)
        self.msg_repo.create(asst_msg)
        
        # Update session timestamp
        self.chat_repo.update_timestamp(session_id)

    def _build_messages(self, session_id: int, current_msg: str, context: str, skill_instruction: str) -> List[Dict]:
        """Construct the message history for the API."""
        # Get history (limit to last 10 for context window efficiency - optimize later)
        history = self.msg_repo.get_session_messages(session_id)
        
        messages = []
        
        # System Prompt
        system_content = "You are a helpful AI assistant."
        if context:
            system_content += f"\n\nUse the following context to answer the user's question:\n{context}"
        
        if skill_instruction:
            system_content += skill_instruction
            
        messages.append({"role": "system", "content": system_content})
        
        # Chat History
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
            
        return messages
