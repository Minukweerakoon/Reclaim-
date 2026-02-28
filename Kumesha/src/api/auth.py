import os

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key_header_value: str = Depends(api_key_header)) -> str:
    """
    Validate API key from header.

    This is intentionally simple: a single shared API key configured via env var `API_KEY`.
    """
    expected_key = os.getenv("API_KEY", "test-api-key")
    if api_key_header_value == expected_key:
        return api_key_header_value
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

