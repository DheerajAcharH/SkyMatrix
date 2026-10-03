import hmac

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_device_key(x_device_key: str | None = Header(default=None)) -> None:
    expected = get_settings().device_api_key
    if not expected or not x_device_key or not hmac.compare_digest(x_device_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Device-Key header is required.",
        )
