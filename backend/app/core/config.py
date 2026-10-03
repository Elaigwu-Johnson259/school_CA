"""
Application configuration.

All settings are loaded from environment variables (see .env.example).
Using pydantic-settings means we get validation and type-checking for free:
if a required setting is missing, the app will fail to start with a clear
error instead of failing mysteriously later.
"""
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174"]

    # File storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 5

    # AI / OCR provider configuration
    AI_PROVIDER: str = "mock"
    AI_MODEL: str = "gpt-4o-mini"
    AI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None
    OPENAI_BASE_URL: str | None = None
    AI_BASE_URL: str | None = None

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_ai_provider(self):
        if self.ENVIRONMENT.lower() == "production":
            if self.AI_PROVIDER.lower() != "openai":
                raise ValueError("Production requires AI_PROVIDER=openai; mock marking is test-only.")
            if not (self.OPENAI_API_KEY or self.AI_API_KEY):
                raise ValueError("Production OpenAI marking requires OPENAI_API_KEY or AI_API_KEY.")
        return self


settings = Settings()
