from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.predictions import router as predictions_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="SkyMatrix Inference API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.web\.app|https://.*\.firebaseapp\.com",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(predictions_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    if not settings.model_path.is_file():
        raise HTTPException(status_code=503, detail="Model weights are unavailable.")
    return {"status": "ok", "model": "ready"}
