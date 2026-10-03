import json
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_path: Path = Path(__file__).resolve().parents[2] / "models" / "best.pt"
    confidence_threshold: float = 0.45
    max_image_bytes: int = 10_000_000
    device_api_key: str = "esp32-cam-skymatrix"
    cloudinary_url: str = ""
    firebase_service_account_json: str = ""
    firebase_service_account_file: Path | None = None
    firestore_database_id: str = "(default)"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "https://skymatrix-hd.web.app",
        "https://skymatrix-hd.firebaseapp.com",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("'") and raw.endswith("'"):
                raw = raw[1:-1].strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
            return [item.strip().strip('"\'') for item in raw.strip('[]').split(',') if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
