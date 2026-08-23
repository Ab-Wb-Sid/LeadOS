from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_internal_api_key(
    x_internal_key: str = Header(
        None, 
        alias="X-Internal-Key", 
        description="Internal API Key for system integrations (e.g. n8n)"
    )
) -> str:
    """
    FastAPI dependency to verify the X-Internal-Key header.
    Checks the header against the INTERNAL_API_KEY from config.
    Raises 401 Unauthorized if the header is missing or incorrect.
    This separates the shared-secret logic from standard user JWT authentication.
    """
    if not x_internal_key or x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal API key",
        )
    return x_internal_key
