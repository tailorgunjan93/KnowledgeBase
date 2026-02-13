"""API service for Groq integration."""
from groq import Groq
from typing import List, Dict, Optional
import streamlit as st


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
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID to use
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
        
        Returns:
            Generated text response
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
                return response  # Return generator for streaming
            else:
                return response.choices[0].message.content
        
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = 'llama-3.1-70b-versatile',
        temperature: float = 0.7,
        max_tokens: int = 8000
    ):
        """
        Get streaming chat completion from Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
        
        Yields:
            Text chunks as they arrive
        """
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            raise Exception(f"Groq API streaming error: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Make a minimal test request
            response = self.client.chat.completions.create(
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
    
    @staticmethod
    def get_model_display_name(model_id: str) -> str:
        """Get display name for a model ID."""
        return APIService.MODELS.get(model_id, model_id)
