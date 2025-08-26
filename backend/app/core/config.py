# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # This is now optional, only needed if you switch back to OpenAI's hosted service
    OPENAI_API_KEY: Optional[str] = "ollama" 

    # New settings for the local LLM
    LOCAL_LLM_MODEL: str = "codestral" # The model you pulled with Ollama
    LOCAL_LLM_URL: str = "http://localhost:11434/v1" # Default Ollama API endpoint

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()