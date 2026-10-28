"""Configuration settings for API test framework."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Central configuration class."""
    BASE_URL: str = os.getenv("BASE_URL", "https://restful-booker.herokuapp.com").rstrip("/")
    API_USERNAME: str = os.getenv("API_USERNAME", "admin")
    API_PASSWORD: str = os.getenv("API_PASSWORD", "password123")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Endpoints
    AUTH_ENDPOINT: str = "/auth"
    BOOKING_ENDPOINT: str = "/booking"
    PING_ENDPOINT: str = "/ping"


settings = Settings()
