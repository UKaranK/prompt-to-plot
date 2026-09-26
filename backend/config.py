import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # LLM Settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite-preview"
    
    # App Settings
    environment: str = "development"
    debug: bool = True
    
    # DB Settings
    duckdb_path: str = "data/sales.duckdb"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
