import requests
from typing import Dict, List, Optional, Union

class DeepSeekAPI:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        """
        Initialize the DeepSeek API client.
        
        Args:
            api_key: Your DeepSeek API key
            base_url: Base URL for the DeepSeek API (default: https://api.deepseek.com/v1)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, 
             model: str, 
             messages: List[Dict[str, str]], 
             temperature: float = 0.7,
             max_tokens: int = 1000,
             **kwargs) -> dict:
        """
        Send a chat completion request to the DeepSeek API.
        
        Args:
            model: The model to use (e.g., "deepseek-chat")
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The API response as a dictionary
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        response = requests.post(
            url,
            headers=self.headers,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
