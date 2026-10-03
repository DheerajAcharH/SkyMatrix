from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_path: Path = Path(__file__).resolve().parents[2] / "models" / "best.pt"
    confidence_threshold: float = 0.45
    max_image_bytes: int = 10_000_000
    device_api_key: str = ""
    cloudinary_url: str = ""
    firebase_service_account_json: str = ""
    firebase_service_account_file: Path | None = None
    firestore_database_id: str = "(default)"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "https://skymatrix-hd.web.app",
        "https://skymatrix-hd.firebaseapp.com",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
