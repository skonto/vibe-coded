from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys - Only OpenAI is required!
    openai_api_key: str  # This is the only required key!
    
    # Redis (default provided)
    redis_url: str = "redis://localhost:6379"
    
    # Security (default provided)
    secret_key: str = "weather_chat_secret_key_change_in_production"
    
    # Application (defaults provided)
    debug: bool = True
    title: str = "Weather Chat API"
    version: str = "1.0.0"
    
    # OpenAI Settings (defaults provided)
    openai_model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # Session Settings (defaults provided)
    session_timeout: int = 3600  # 1 hour in seconds
    max_history_length: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow environment variables to override defaults
        env_prefix = ""
        # Allow extra fields (for backwards compatibility)
        extra = "ignore"


settings = Settings() 