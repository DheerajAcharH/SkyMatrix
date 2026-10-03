import base64

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.security import require_device_key
from app.repositories.cloud_prediction_repository import CloudPredictionRepository
from app.schemas.prediction import InferenceTestResult, PredictionList, PredictionRecord
from app.services.inference_service import predict

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


@router.post("/test", response_model=InferenceTestResult)
async def test_prediction(
    image: UploadFile = File(...),
    _: None = Depends(require_device_key),
) -> InferenceTestResult:
    settings = get_settings()
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG or PNG image.")

    image_bytes = await image.read(settings.max_image_bytes + 1)
    if not image_bytes or len(image_bytes) > settings.max_image_bytes:
        raise HTTPException(status_code=413, detail="Image is empty or exceeds the 10 MB limit.")

    try:
        detections, annotated_image = await run_in_threadpool(predict, image_bytes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail="Model weights are unavailable.") from error

    encoded_image = base64.b64encode(annotated_image).decode("ascii")
    return InferenceTestResult(
        detections=detections,
        annotated_image=f"data:image/jpeg;base64,{encoded_image}",
    )


@router.post("", response_model=PredictionRecord, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    image: UploadFile = File(...),
    latitude: float | None = Form(default=None, ge=-90, le=90),
    longitude: float | None = Form(default=None, ge=-180, le=180),
    device_id: str = Form(default="esp32-cam-01", max_length=80),
    _: None = Depends(require_device_key),
) -> PredictionRecord:
    settings = get_settings()
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG or PNG image.")

    image_bytes = await image.read(settings.max_image_bytes + 1)
    if not image_bytes or len(image_bytes) > settings.max_image_bytes:
        raise HTTPException(status_code=413, detail="Image is empty or exceeds the 10 MB limit.")

    try:
        detections, annotated_image = await run_in_threadpool(predict, image_bytes)
        repository = CloudPredictionRepository()
        record = await run_in_threadpool(
            repository.save_prediction,
            annotated_image,
            [item.model_dump() for item in detections],
            latitude,
            longitude,
            device_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail="Model weights are unavailable.") from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="Inference or cloud persistence failed.") from error

    return PredictionRecord.model_validate(record)


@router.get("", response_model=PredictionList)
def list_predictions(limit: int = 25) -> PredictionList:
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100.")
    try:
        records = CloudPredictionRepository().list_predictions(limit)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Prediction history is unavailable.") from error
    return PredictionList(items=[PredictionRecord.model_validate(record) for record in records])
