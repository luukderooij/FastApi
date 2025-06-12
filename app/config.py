from pydantic_settings import BaseSettings
from typing import Any, Dict, Optional, List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tournament Backend API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 dagen
    SQLALCHEMY_DATABASE_URI: str
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:8080", "http://localhost:3000"]

    # Email configuratie
    MAIL_FROM: str = "noreply@tournamentapp.com"
    SMTP_SERVER: str = "smtp.mailserver.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    
    # Frontend URL voor links in emails
    FRONTEND_URL: str = "http://localhost:3000"




    class Config:
        case_sensitive = True
        env_file = ".env"  # Hier specificeren we het .env bestand
        env_file_encoding = "utf-8"


settings = Settings()