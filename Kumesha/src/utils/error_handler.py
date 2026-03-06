"""
Error response helper utilities for consistent API error handling.
"""
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a consistent error response.
    
    Args:
        status_code: HTTP status code
        error_code: Application-specific error code
        message: User-friendly error message
        details: Optional additional error details
        
    Returns:
        JSONResponse with standardized error format
    """
    error_body = {
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code
        }
    }
    
    if details:
        error_body["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_body
    )


def handle_validation_error(e: Exception, context: str = "") -> JSONResponse:
    """
    Handle validation errors and return appropriate response.
    
    Args:
        e: The exception that occurred
        context: Context about where the error occurred
        
    Returns:
        JSONResponse with error details
    """
    logger.error(f"Validation error in {context}: {str(e)}")
    
    # Map exception types to HTTP status codes
    from src.utils.exceptions import (
        FileFormatError,
        FileSizeError,
        ModelLoadError,
        APIRateLimitError,
        NetworkError,
        DatabaseError,
        ImageValidationError,
        TextValidationError,
        VoiceValidationError
    )
    
    if isinstance(e, FileFormatError):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="FILE_FORMAT_ERROR",
            message="Invalid file format. Please upload a JPEG, PNG, or WebP image.",
            details={"allowed_formats": e.allowed_formats} if hasattr(e, 'allowed_formats') else None
        )
    
    elif isinstance(e, FileSizeError):
        return create_error_response(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_SIZE_ERROR",
            message=f"File too large. Maximum size is {e.max_size_mb}MB.",
            details={"max_size_mb": e.max_size_mb} if hasattr(e, 'max_size_mb') else None
        )
    
    elif isinstance(e, ModelLoadError):
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="MODEL_LOAD_ERROR",
            message="AI model failed to load. Please try again later."
        )
    
    elif isinstance(e, APIRateLimitError):
        return create_error_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR",
            message=f"Too many requests. Please wait {e.retry_after} seconds.",
            details={"retry_after": e.retry_after} if hasattr(e, 'retry_after') else None
        )
    
    elif isinstance(e, NetworkError):
        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="NETWORK_ERROR",
            message="External service unavailable. Please try again.",
            details={"service": e.service} if hasattr(e, 'service') else None
        )
    
    elif isinstance(e, (ImageValidationError, TextValidationError, VoiceValidationError)):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=e.error_code,
            message=str(e)
        )
    
    elif isinstance(e, DatabaseError):
        logger.warning(f"Database error (non-critical): {str(e)}")
        # Database errors are non-blocking, just log and continue
        return None
    
    else:
        # Generic error
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again."
        )


def validate_file_upload(file: Any, allowed_types: list, max_size_mb: int = 10) -> None:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file object
        allowed_types: List of allowed MIME types
        max_size_mb: Maximum file size in MB
        
    Raises:
        FileFormatError: If file type is not allowed
        FileSizeError: If file is too large
    """
    from src.utils.exceptions import FileFormatError, FileSizeError
    
    # Check file type
    if hasattr(file, 'content_type') and file.content_type not in allowed_types:
        raise FileFormatError(
            f"Invalid file type: {file.content_type}",
            allowed_formats=allowed_types
        )
    
    # Check file size
    if hasattr(file, 'size') and file.size:
        max_bytes = max_size_mb * 1024 * 1024
        if file.size > max_bytes:
            raise FileSizeError(
                f"File size {file.size / 1024 / 1024:.1f}MB exceeds {max_size_mb}MB limit",
                max_size_mb=max_size_mb
            )
