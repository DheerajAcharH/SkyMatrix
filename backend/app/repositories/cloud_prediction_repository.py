import json
from datetime import datetime, timezone
from functools import lru_cache
from io import BytesIO
from urllib.parse import unquote, urlparse

import cloudinary
import cloudinary.uploader
import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import get_settings


@lru_cache(maxsize=1)
def _firestore_client():
    try:
        app = firebase_admin.get_app()
    except ValueError:
        raw_credentials = get_settings().firebase_service_account_json
        if not raw_credentials:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON must be configured.")
        app = firebase_admin.initialize_app(credentials.Certificate(json.loads(raw_credentials)))
    return firestore.client(app=app, database_id=get_settings().firestore_database_id)


class CloudPredictionRepository:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.cloudinary_url:
            raise RuntimeError("CLOUDINARY_URL must be configured.")
        cloudinary_url = urlparse(settings.cloudinary_url)
        if cloudinary_url.scheme != "cloudinary" or not all(
            (cloudinary_url.hostname, cloudinary_url.username, cloudinary_url.password)
        ):
            raise RuntimeError("CLOUDINARY_URL is invalid.")
        cloudinary.config(
            cloud_name=cloudinary_url.hostname,
            api_key=unquote(cloudinary_url.username),
            api_secret=unquote(cloudinary_url.password),
            secure=True,
        )
        self.predictions = _firestore_client().collection("predictions")

    def save_prediction(
        self,
        annotated_image: bytes,
        detections: list[dict],
        latitude: float | None,
        longitude: float | None,
        device_id: str,
    ) -> dict:
        upload = cloudinary.uploader.upload(
            BytesIO(annotated_image),
            resource_type="image",
            folder="skymatrix/predictions",
            format="jpg",
            tags=["skymatrix", device_id],
        )
        created_at = datetime.now(timezone.utc)
        record = {
            "created_at": created_at,
            "image_url": upload["secure_url"],
            "cloudinary_public_id": upload["public_id"],
            "detection_count": len(detections),
            "detections": detections,
            "latitude": latitude,
            "longitude": longitude,
            "device_id": device_id,
        }
        try:
            document = self.predictions.document()
            document.set(record)
        except Exception:
            cloudinary.uploader.destroy(upload["public_id"], resource_type="image")
            raise
        return {"id": document.id, **record}

    def list_predictions(self, limit: int) -> list[dict]:
        documents = (
            self.predictions.order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        records = []
        for document in documents:
            record = document.to_dict()
            created_at = record.get("created_at")
            if hasattr(created_at, "isoformat"):
                record["created_at"] = created_at.isoformat()
            records.append({"id": document.id, **record})
        return records