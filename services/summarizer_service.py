"""Summarizer Service."""
from services.chat_service import ChatService
from services.file_processing.parser import FileParserService
from domain.exceptions import ExternalServiceError

class SummarizerService:
    """
    Service for generating document summaries using the LLM.
    Uses ChatService's underlying API client but tailored prompt.
    """
    
    def __init__(self):
        self.chat_service = ChatService()
        self.parser = FileParserService()

    def generate_summary(self, text: str, length: str = "medium", style: str = "bullet_points", user_id: int = None) -> str:
        """
        Generate a summary of the provided text.
        """
        # Construct Prompt
        length_prompt = {
            "short": "concise (1-2 paragraphs)",
            "medium": "detailed (3-5 paragraphs)",
            "long": "comprehensive (detailed analysis)"
        }.get(length, "medium")
        
        style_prompt = {
            "bullet_points": "Use bullet points for key takeaways.",
            "paragraph": "Write in flowing paragraphs.",
            "executive": "Format as an executive summary with headers."
        }.get(style, "bullet points")
        
        system_msg = f"You are an expert summarizer. Summarize the text to be {length_prompt}. {style_prompt}"
        user_msg = f"Text to summarize:\n\n{text[:25000]}" # Limit context window brute force for now
        
        # Call LLM via ChatService logic reuse or direct client
        # Reusing client retrieval logic
        client = self.chat_service._get_api_client(user_id)
        
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                model="llama-3.1-70b-versatile",
                temperature=0.5
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ExternalServiceError(f"Summarization failed: {e}")
