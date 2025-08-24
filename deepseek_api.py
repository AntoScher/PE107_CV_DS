import json
import time
import requests
from typing import Dict, List, Optional, Union, Any
from config import config
from logger import get_logger, log_performance, log_errors

# Initialize logger
logger = get_logger("deepseek_api")

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
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None
    ):
        """
        Initialize the DeepSeek API client.
        
        Args:
            api_key: Your DeepSeek API key
            base_url: Base URL for the DeepSeek API (uses config default if None)
            timeout: Request timeout in seconds (uses config default if None)
            max_retries: Maximum number of retry attempts for failed requests (uses config default if None)
            retry_delay: Delay between retry attempts in seconds (uses config default if None)
        """
        if not api_key:
            raise ValueError("API key is required")
        
        logger.info("Initializing DeepSeek API client")
            
        self.api_key = api_key
        self.base_url = (base_url or config.api.base_url).rstrip('/')
        self.timeout = timeout or config.api.timeout
        self.max_retries = max_retries or config.api.max_retries
        self.retry_delay = retry_delay or config.api.retry_delay
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"DeepSeek API client initialized with base_url: {self.base_url}")
    
    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle API error responses and raise appropriate exceptions."""
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'unknown')
        except (ValueError, AttributeError):
            error_msg = response.text or 'Unknown error'
            error_code = 'unknown'
        
        logger.error(f"API error response: {response.status_code} - {error_msg} (code: {error_code})")
        
        logger.debug(f"Processing status code: {response.status_code}")
        
        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_msg}")
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After', self.retry_delay)
            raise RateLimitError(f"Rate limit exceeded. Try again in {retry_after} seconds")
        elif 400 <= response.status_code < 500:
            logger.debug(f"Raising DeepSeekAPIError for status code {response.status_code}")
            raise DeepSeekAPIError(f"API request failed ({response.status_code}): {error_msg}")
        elif response.status_code == 500:
            # For 500 errors, raise HTTPError
            logger.debug(f"Raising HTTPError for status code {response.status_code}")
            response.raise_for_status()
        elif response.status_code >= 500:
            # For 5xx errors, raise HTTPError
            logger.debug(f"Raising HTTPError for status code {response.status_code}")
            response.raise_for_status()
        else:
            # For other errors, raise HTTPError
            logger.debug(f"Raising HTTPError for status code {response.status_code}")
            response.raise_for_status()
    
    @log_performance(logger)
    @log_errors(logger)
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        last_exception = None
        
        logger.debug(f"Making {method} request to {endpoint}")
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Request attempt {attempt + 1}/{self.max_retries + 1}")
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    logger.debug("Request successful")
                    return response.json()
                
                self._handle_error_response(response)
                
            except (requests.exceptions.RequestException, 
                  DeepSeekAPIError) as e:
                last_exception = e
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries and not isinstance(e, AuthenticationError):
                    sleep_time = self.retry_delay * (attempt + 1)
                    logger.debug(f"Waiting {sleep_time}s before retry")
                    time.sleep(sleep_time)
                    continue
                raise
        
        logger.error(f"All {self.max_retries + 1} request attempts failed")
        raise last_exception or DeepSeekAPIError("Request failed after maximum retries")

    @log_performance(logger)
    @log_errors(logger)
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the DeepSeek API.
        
        Args:
            model: The model to use (e.g., "deepseek-chat")
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Sampling temperature (0-2). Lower values make output more deterministic. (uses config default if None)
            max_tokens: Maximum number of tokens to generate (uses config default if None)
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
        
        # Use config defaults if not provided
        temperature = temperature if temperature is not None else config.api.temperature
        max_tokens = max_tokens if max_tokens is not None else config.api.max_tokens
        
        logger.info(f"Sending chat request to model: {model}, temperature: {temperature}, max_tokens: {max_tokens}")
            
        payload = {
            "model": model,
            "messages": messages,
            "temperature": max(0, min(2, temperature)),  # Clamp to 0-2 range
            "max_tokens": max(1, min(4000, max_tokens)),  # Clamp to 1-4000 range
            **kwargs
        }
        
        logger.debug(f"Chat payload prepared with {len(messages)} messages")
        
        return self._make_request(
            method="POST",
            endpoint="/chat/completions",
            json=payload
        )
    
    @log_performance(logger)
    @log_errors(logger)
    def get_models(self) -> Dict[str, Any]:
        """
        List available models.
        
        Returns:
            Dictionary containing available models
        """
        logger.info("Fetching available models")
        return self._make_request("GET", "/models")
