"""
Custom exceptions for the multimodal validation system.
Provides specific, user-friendly error messages.
"""

class ValidationError(Exception):
    """Base exception for validation errors."""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ImageValidationError(ValidationError):
    """Raised when image validation fails."""
    def __init__(self, message: str):
        super().__init__(message, "IMAGE_VALIDATION_ERROR")


class FileFormatError(ValidationError):
    """Raised when file format is invalid."""
    def __init__(self, message: str, allowed_formats: list = None):
        self.allowed_formats = allowed_formats or []
        super().__init__(message, "FILE_FORMAT_ERROR")


class FileSizeError(ValidationError):
    """Raised when file size exceeds limits."""
    def __init__(self, message: str, max_size_mb: int = 10):
        self.max_size_mb = max_size_mb
        super().__init__(message, "FILE_SIZE_ERROR")


class ModelLoadError(ValidationError):
    """Raised when AI model fails to load."""
    def __init__(self, message: str, model_name: str = ""):
        self.model_name = model_name
        super().__init__(message, "MODEL_LOAD_ERROR")


class APIRateLimitError(ValidationError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR")


class NetworkError(ValidationError):
    """Raised when network/external service fails."""
    def __init__(self, message: str, service: str = ""):
        self.service = service
        super().__init__(message, "NETWORK_ERROR")


class DatabaseError(ValidationError):
    """Raised when database operations fail."""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


class TextValidationError(ValidationError):
    """Raised when text validation fails."""
    def __init__(self, message: str):
        super().__init__(message, "TEXT_VALIDATION_ERROR")


class VoiceValidationError(ValidationError):
    """Raised when voice validation fails."""
    def __init__(self, message: str):
        super().__init__(message, "VOICE_VALIDATION_ERROR")


# User-friendly error messages
ERROR_MESSAGES = {
    "FILE_FORMAT_ERROR": "Invalid file format. Please upload a JPEG, PNG, or WebP image.",
    "FILE_SIZE_ERROR": "File too large. Maximum size is {max_size}MB.",
    "IMAGE_TOO_BLURRY": "Image is too blurry. Please retake with better focus.",
    "NO_OBJECTS_DETECTED": "No clear objects detected. Try better lighting and positioning.",
    "MODEL_LOAD_ERROR": "AI model failed to load. Please try again.",
    "RATE_LIMIT_ERROR": "Too many requests. Please wait {retry_after} seconds.",
    "NETWORK_ERROR": "Network error connecting to {service}. Please check your connection.",
    "DATABASE_ERROR": "Database error. Your data may not be saved.",
    "INVALID_AUDIO_FORMAT": "Invalid audio format. Browser should send WebM or MP3.",
    "TRANSCRIPTION_FAILED": "Could not transcribe audio. Please speak clearly and try again.",
    "TEXT_TOO_SHORT": "Description too short. Please provide more details (minimum 10 characters).",
    "MISSING_REQUIRED_FIELD": "Missing required information: {field}",
}


def get_user_friendly_message(error_code: str, **kwargs) -> str:
    """Get user-friendly error message with placeholders filled."""
    template = ERROR_MESSAGES.get(error_code, "An error occurred. Please try again.")
    return template.format(**kwargs)
