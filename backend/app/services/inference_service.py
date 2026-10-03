from functools import lru_cache
from io import BytesIO
from threading import Lock

import cv2
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

from app.core.config import get_settings
from app.schemas.prediction import Detection

_model_lock = Lock()


@lru_cache(maxsize=1)
def _load_model() -> YOLO:
    model_path = get_settings().model_path
    if not model_path.is_file():
        raise FileNotFoundError(f"Model weights not found: {model_path}")
    return YOLO(str(model_path))


def predict(image_bytes: bytes) -> tuple[list[Detection], bytes]:
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError("Uploaded file is not a supported image.") from error

    with _model_lock:
        result = _load_model().predict(
            source=image,
            conf=get_settings().confidence_threshold,
            verbose=False,
        )[0]

    annotated = result.plot()
    encoded, jpeg = cv2.imencode(".jpg", annotated)
    if not encoded:
        raise RuntimeError("Could not encode the annotated frame.")

    detections = []
    names = result.names
    for box in result.boxes:
        class_id = int(box.cls.item())
        label = names.get(class_id, str(class_id)) if isinstance(names, dict) else names[class_id]
        detections.append(
            Detection(
                class_id=class_id,
                label=str(label),
                confidence=float(box.conf.item()),
                box=[float(value) for value in box.xyxy[0].tolist()],
            )
        )
    return detections, jpeg.tobytes()
