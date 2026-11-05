import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Settings:

    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "DealPilot AI Backend")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    API_V1_STR: str = os.getenv("API_V1_STR", "/api")

    # Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")

    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "dealpilot")

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,"
            "http://127.0.0.1:3000,"
            "http://localhost:8000,"
            "http://127.0.0.1:8000,"
            "http://localhost:5500,"
            "http://127.0.0.1:5500"
        ).split(",")
        if origin.strip()
    ]

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Channel3 API
    CHANNEL3_API_KEY: Optional[str] = os.getenv("CHANNEL3_API_KEY")

    CHANNEL3_BASE_URL: str = os.getenv("CHANNEL3_BASE_URL", "https://api.channel3.ai/v1")

    # PayPal Sandbox
    PAYPAL_CLIENT_ID: str = os.getenv("PAYPAL_CLIENT_ID", "")

    PAYPAL_CLIENT_SECRET: str = os.getenv("PAYPAL_CLIENT_SECRET", "")

    PAYPAL_BASE_URL: str = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")

    PAYPAL_WEBHOOK_ID: Optional[str] = os.getenv("PAYPAL_WEBHOOK_ID")


settings = Settings()