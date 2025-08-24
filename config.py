"""
Configuration settings for the AI Resume Analyzer application.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class APIConfig:
    """API configuration settings."""
    base_url: str = "https://api.deepseek.com/v1"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    max_tokens: int = 1000
    temperature: float = 0.0

@dataclass
class ParserConfig:
    """Parser configuration settings."""
    max_retries: int = 3
    timeout: int = 10
    user_agents: Optional[list] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            ]

@dataclass
class AppConfig:
    """Application configuration settings."""
    debug: bool = False
    log_level: str = "INFO"
    cache_timeout: int = 3600  # 1 hour
    max_input_length: int = 10000
    supported_domains: Optional[list] = None
    
    def __post_init__(self):
        if self.supported_domains is None:
            self.supported_domains = ["hh.ru"]

class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.api = APIConfig()
        self.parser = ParserConfig()
        self.app = AppConfig()
        
        # Load environment variables
        self._load_env_vars()
    
    def _load_env_vars(self):
        """Load configuration from environment variables."""
        # API settings
        if os.getenv("DEEPSEEK_BASE_URL"):
            self.api.base_url = os.getenv("DEEPSEEK_BASE_URL")
        if os.getenv("DEEPSEEK_TIMEOUT"):
            self.api.timeout = int(os.getenv("DEEPSEEK_TIMEOUT"))
        if os.getenv("DEEPSEEK_MAX_RETRIES"):
            self.api.max_retries = int(os.getenv("DEEPSEEK_MAX_RETRIES"))
        
        # Parser settings
        if os.getenv("PARSER_TIMEOUT"):
            self.parser.timeout = int(os.getenv("PARSER_TIMEOUT"))
        if os.getenv("PARSER_MAX_RETRIES"):
            self.parser.max_retries = int(os.getenv("PARSER_MAX_RETRIES"))
        
        # App settings
        if os.getenv("DEBUG"):
            self.app.debug = os.getenv("DEBUG").lower() in ("true", "1", "yes")
        if os.getenv("LOG_LEVEL"):
            self.app.log_level = os.getenv("LOG_LEVEL").upper()
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment or secrets."""
        # Try environment variable first
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            return api_key
        
        # Try Streamlit secrets (for deployed apps)
        try:
            import streamlit as st
            return st.secrets.get("DEEPSEEK_API_KEY")
        except (ImportError, AttributeError):
            return None
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        errors = []
        
        # Validate API settings
        if self.api.timeout <= 0:
            errors.append("API timeout must be positive")
        if self.api.max_retries < 0:
            errors.append("API max retries cannot be negative")
        if not (0 <= self.api.temperature <= 2):
            errors.append("API temperature must be between 0 and 2")
        
        # Validate parser settings
        if self.parser.timeout <= 0:
            errors.append("Parser timeout must be positive")
        if self.parser.max_retries < 0:
            errors.append("Parser max retries cannot be negative")
        
        # Validate app settings
        if self.app.cache_timeout < 0:
            errors.append("Cache timeout cannot be negative")
        if self.app.max_input_length <= 0:
            errors.append("Max input length must be positive")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True

# Global configuration instance
config = Config()

# System prompt template
SYSTEM_PROMPT_TEMPLATE = """
Проскорь кандидата, насколько он подходит для данной вакансии.

Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?).
Эта оценка должна учитываться при выставлении финальной оценки - нам важно нанимать таких кандидатов, которые могут рассказать про свою работу.
Потом представь результат в виде оценки от 1 до 10.
""".strip()

# Default headers for HTTP requests
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
