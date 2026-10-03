from datetime import datetime

from pydantic import BaseModel, Field


class Detection(BaseModel):
    class_id: int
    label: str
    confidence: float
    box: list[float] = Field(min_length=4, max_length=4)


class PredictionRecord(BaseModel):
    id: str
    created_at: datetime
    detection_count: int
    detections: list[Detection]
    image_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    device_id: str


class PredictionList(BaseModel):
    items: list[PredictionRecord]


class InferenceTestResult(BaseModel):
    detections: list[Detection]
    annotated_image: str
