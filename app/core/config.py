# app/core/config.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    STRIPE_SECRET_KEY: str
    STRIPE_ENDPOINT_SECRET: str
    LOB_API_KEY: str
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    CUPS_SERVER_HOST: str
    CUPS_SERVER_PORT: int

    model_config = SettingsConfigDict(env_file=str(ENV_FILE))

settings = Settings()

