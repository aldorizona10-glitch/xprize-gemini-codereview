"""
CodeLens AI - Gemini-Powered Code Review SaaS
Configuration module
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "CodeLens AI"
    APP_VERSION: str = "1.0.0"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEMO_MODE: bool = True
    STRIPE_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
