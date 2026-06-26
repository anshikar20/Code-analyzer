"""
Centralized configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Application
    app_name: str = "Realtime Source Code Analyzer"
    app_version: str = "2.0.0"
    debug: bool = False

    # CORS
    allowed_origins: list[str] = ["*"]

    # Gemini AI
    gemini_api_key: str = ""
    gemini_primary_model: str = "gemini-2.5-pro"
    gemini_fallback_model: str = "gemini-2.5-flash"
    gemini_timeout: int = 30

    # Analysis
    tool_timeout: int = 30
    max_code_length: int = 100_000  # 100KB max

    # Custom Rules
    custom_rules_file: str = "custom_rules.json"

    # Supported Languages
    supported_languages: list[str] = ["python", "java", "cpp"]

    model_config = {
        "env_file": ".env",
        "env_prefix": "ANALYZER_",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    from dotenv import load_dotenv
    import os
    load_dotenv()
    settings = Settings()
    if not settings.gemini_api_key:
        settings.gemini_api_key = os.environ.get("ANALYZER_GEMINI_API_KEY", "")
    return settings
