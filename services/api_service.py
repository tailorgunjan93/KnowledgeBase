"""API service for Groq integration."""
from groq import Groq
from typing import List, Dict

class APIService:
    """Handles communication with Groq API."""
    
    # Available models
    MODELS = {
        'llama-3.3-70b-versatile': 'Llama 3.3 70B',
        'llama-3.1-70b-versatile': 'Llama 3.1 70B',
        'llama-3.1-8b-instant': 'Llama 3.1 8B',
        'mixtral-8x7b-32768': 'Mixtral 8x7B',
        'gemma2-9b-it': 'Gemma 2 9B',
    }
    
    def __init__(self, api_key: str):
        """
        Initialize Groq API client.
        
        Args:
            api_key: Groq API key
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.client = Groq(api_key=api_key)
        self.api_key = api_key
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = 'llama-3.1-70b-versatile',
        temperature: float = 0.7,
        max_tokens: int = 8000,
        stream: bool = False
    ) -> str:
        """
        Get chat completion from Groq API.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response
            else:
                return response.choices[0].message.content
        
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request.
        """
        try:
            # Make a minimal test request
            self.client.chat.completions.create(
                model='llama-3.1-8b-instant',
                messages=[{'role': 'user', 'content': 'Hi'}],
                max_tokens=5
            )
            return True
        except:
            return False
    
    @staticmethod
    def get_available_models() -> Dict[str, str]:
        """Get dictionary of available models."""
        return APIService.MODELS
