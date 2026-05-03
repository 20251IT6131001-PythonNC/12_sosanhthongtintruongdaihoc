from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import json
import os


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), '../.env'),
        extra='allow'
    )

    # Database
    DATABASE_HOST: str
    DATABASE_PORT: int = 3306
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]'

    # Gemini AI (for chatbot)
    GEMINI_KEY: str = ""

    # Tavily (online search fallback when DB data is insufficient)
    TAVILY_API_KEY: str = ""

    # Email Configuration (Gmail SMTP)
    GMAIL_SENDER_EMAIL: str = "your-email@gmail.com"
    GMAIL_APP_PASSWORD: str = "your-app-specific-password"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_FROM_NAME: str = "UniCompare"
    EMAIL_VERIFICATION_ENABLED: bool = True
    EMAIL_VERIFICATION_EXPIRY_HOURS: int = 24
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string to list"""
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
