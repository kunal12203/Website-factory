# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AI_PROVIDER: str = "openai"
    AI_TEMPERATURE: float = 0.5

    # Model names for each provider
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"

    # --- START: NEW MAX TOKENS CONFIG ---
    # Max output tokens for each provider
    OPENAI_MAX_TOKENS: int = 8192
    ANTHROPIC_MAX_TOKENS: int = 4096 # Respect Haiku's limit
    
    # This property dynamically returns the correct model name
    @property
    def AI_MODEL(self) -> str:
        if self.AI_PROVIDER.lower() == "anthropic":
            return self.ANTHROPIC_MODEL
        return self.OPENAI_MODEL

    # This property dynamically returns the correct max_tokens limit
    @property
    def AI_MAX_TOKENS(self) -> int:
        if self.AI_PROVIDER.lower() == "anthropic":
            return self.ANTHROPIC_MAX_TOKENS
        return self.OPENAI_MAX_TOKENS
    # --- END: NEW MAX TOKENS CONFIG ---

    # API Keys
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # --- NEW MYSQL SETTINGS ---
    DB_HOST: str = "localhost"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "website_factory_kb"
    
    model_config = SettingsConfigDict(env_file=".env")

    

settings = Settings()