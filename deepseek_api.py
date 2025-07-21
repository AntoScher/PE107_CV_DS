import json
import time
import requests
from typing import Dict, List, Optional, Union, Any

class DeepSeekAPIError(Exception):
    """Base exception for DeepSeek API errors."""
    pass

class RateLimitError(DeepSeekAPIError):
    """Raised when the API rate limit is exceeded."""
    pass

class AuthenticationError(DeepSeekAPIError):
    """Raised when authentication fails."""
    pass

class DeepSeekAPI:
    """A client for the DeepSeek API with retry logic and error handling."""
    
    def __init__(self, 
                api_key: str, 
                base_url: str = "https://api.deepseek.com/v1",
                timeout: int = 30,
                max_retries: int = 3,
                retry_delay: int = 5):
        """
        Initialize the DeepSeek API client.
        
        Args:
            api_key: Your DeepSeek API key
            base_url: Base URL for the DeepSeek API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
        """
        if not api_key:
            raise ValueError("API key is required")
            
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle API error responses and raise appropriate exceptions."""
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'unknown')
        except (ValueError, AttributeError):
            error_msg = response.text or 'Unknown error'
            error_code = 'unknown'
        
        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_msg}")
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After', self.retry_delay)
            raise RateLimitError(f"Rate limit exceeded. Try again in {retry_after} seconds")
        elif 400 <= response.status_code < 500:
            raise DeepSeekAPIError(f"API request failed ({response.status_code}): {error_msg}")
        else:
            response.raise_for_status()
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return response.json()
                
                self._handle_error_response(response)
                
            except (requests.exceptions.RequestException, 
                  DeepSeekAPIError) as e:
                last_exception = e
                if attempt < self.max_retries and not isinstance(e, AuthenticationError):
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise
        
        raise last_exception or DeepSeekAPIError("Request failed after maximum retries")
    
    def chat(self, 
             model: str, 
             messages: List[Dict[str, str]], 
             temperature: float = 0.7,
             max_tokens: int = 1000,
             **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to the DeepSeek API.
        
        Args:
            model: The model to use (e.g., "deepseek-chat")
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Sampling temperature (0-2). Lower values make output more deterministic.
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The API response as a dictionary
            
        Raises:
            DeepSeekAPIError: For API-related errors
            requests.exceptions.RequestException: For network-related errors
        """
        if not model:
            raise ValueError("Model name is required")
            
        if not messages or not isinstance(messages, list):
            raise ValueError("Messages must be a non-empty list")
            
        payload = {
            "model": model,
            "messages": messages,
            "temperature": max(0, min(2, temperature)),  # Clamp to 0-2 range
            "max_tokens": max(1, min(4000, max_tokens)),  # Clamp to 1-4000 range
            **kwargs
        }
        
        return self._make_request(
            method="POST",
            endpoint="/chat/completions",
            json=payload
        )
    
    def get_models(self) -> Dict[str, Any]:
        """
        List available models.
        
        Returns:
            Dictionary containing available models
        """
        return self._make_request("GET", "/models")
