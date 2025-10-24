import os
import time
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from multimodal_validator import MultimodalValidator
from text_validator import TextValidator
from audio_validator import AudioValidator
from clip_validator import CLIPValidator
from image_validator import ImageValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('validation-api')

# Initialize FastAPI app
app = FastAPI(
    title="Multimodal Validation API",
    description="A comprehensive validation system for multimodal inputs including images, text, and audio.",
    version="1.0.0"
)

# API Key security scheme
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Rate limiting settings
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # requests per window
rate_limit_storage = {}  # IP -> {count: int, reset_time: float}

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File upload settings
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_AUDIO_TYPES = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/m4a"]

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize validators
multimodal_validator = MultimodalValidator(enable_logging=True)
text_validator = TextValidator()
audio_validator = AudioValidator()
clip_validator = CLIPValidator()
image_validator = ImageValidator()

# Active WebSocket connections for progress updates
active_connections = {}

# Performance metrics
metrics = {
    "requests": 0,
    "successful_validations": 0,
    "failed_validations": 0,
    "avg_response_time": 0,
    "total_response_time": 0,
    "start_time": time.time()
}

# Background tasks in progress
background_tasks_progress = {}

# API Key validation
def get_api_key(api_key_header: str = Depends(api_key_header)):
    """
    Validate API key from header. In a production environment, this would
    check against a database of valid API keys.
    """
    # For demo purposes, we're using a hardcoded API key
    # In production, use a secure database or service for API key validation
    if api_key_header == "test-api-key":
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        current_time = time.time()
        
        # Check if client is in rate limit storage
        if client_ip in rate_limit_storage:
            client_data = rate_limit_storage[client_ip]
            
            # Reset count if window has passed
            if current_time > client_data["reset_time"]:
                rate_limit_storage[client_ip] = {
                    "count": 1,
                    "reset_time": current_time + RATE_LIMIT_WINDOW
                }
            else:
                # Increment count and check limit
                client_data["count"] += 1
                if client_data["count"] > RATE_LIMIT_MAX_REQUESTS:
                    return JSONResponse(
                        status_code=HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Rate limit exceeded",
                            "reset_at": client_data["reset_time"]
                        }
                    )
        else:
            # First request from this client
            rate_limit_storage[client_ip] = {
                "count": 1,
                "reset_time": current_time + RATE_LIMIT_WINDOW
            }
        
        # Process the request
        response = await call_next(request)
        return response

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Request/response logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip logging for certain paths
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
        
        # Update metrics
        metrics["requests"] += 1
        metrics["total_response_time"] += process_time
        metrics["avg_response_time"] = metrics["total_response_time"] / metrics["requests"]
        
        return response

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Pydantic models for request/response validation
class ValidationResponse(BaseModel):
    valid: bool
    confidence: float
    confidence_interval: Optional[List[float]] = None
    routing: Optional[str] = None
    modal_scores: Dict[str, Any]
    consistency: Optional[Dict[str, Any]] = None
    feedback: Dict[str, Any]
    processing_time: float
    message: str
    request_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))

class TextValidationRequest(BaseModel):
    text: str
    language: str = "en"  # use "auto" to enable language detection

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    path: Optional[str] = None
    suggestion: Optional[str] = None

# Helper functions
def save_uploaded_file(upload_file: UploadFile) -> str:
    """
    Save an uploaded file to disk and return the file path.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = f"{timestamp}_{upload_file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())
    
    return file_path

def validate_file_type(file: UploadFile, allowed_types: List[str]) -> bool:
    """
    Validate that the uploaded file is of an allowed type.
    """
    return file.content_type in allowed_types

def validate_file_size(file: UploadFile, max_size: int) -> bool:
    """
    Validate that the uploaded file is within the size limit.
    """
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset file pointer
    return file_size <= max_size

async def cleanup_file(file_path: str, delay: int = 300):
    """
    Delete a file after a specified delay (in seconds).
    """
    await asyncio.sleep(delay)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")

async def update_progress(websocket_id: str, progress: int, message: str):
    """
    Send progress updates to a WebSocket client.
    """
    if websocket_id in active_connections:
        websocket = active_connections[websocket_id]
        try:
            await websocket.send_json({
                "progress": progress,
                "message": message
            })
        except Exception as e:
            logger.error(f"Error sending progress update: {str(e)}")

async def process_validation_background(task_id: str, text: Optional[str], image_path: Optional[str], audio_path: Optional[str], language: str):
    """
    Process validation in the background and update progress.
    """
    try:
        # Update progress to 10%
        background_tasks_progress[task_id] = {"progress": 10, "message": "Starting validation"}
        await update_progress(task_id, 10, "Starting validation")
        
        # Update progress to 30%
        background_tasks_progress[task_id] = {"progress": 30, "message": "Processing inputs"}
        await update_progress(task_id, 30, "Processing inputs")
        
        # Perform validation with progress callbacks
        def cb(evt: dict):
            # Stream intermediate confidence and stage updates
            if "confidence" in evt:
                background_tasks_progress[task_id] = {**background_tasks_progress.get(task_id, {}), "progress": background_tasks_progress.get(task_id, {}).get("progress", 50), "message": "Updating confidence", "confidence": evt.get("confidence"), "ci": evt.get("ci")}
            elif evt.get("type") == "stage":
                background_tasks_progress[task_id] = {**background_tasks_progress.get(task_id, {}), "message": evt.get("message", "Processing"), "stage": evt.get("stage")}
            asyncio.create_task(update_progress(task_id, background_tasks_progress.get(task_id, {}).get("progress", 50), background_tasks_progress.get(task_id, {}).get("message", "Processing")))

        result = multimodal_validator.validate(text, image_path, audio_path, language, progress_cb=cb)
        
        # Update progress to 90%
        background_tasks_progress[task_id] = {"progress": 90, "message": "Finalizing results"}
        await update_progress(task_id, 90, "Finalizing results")
        
        # Add task_id to result
        result["request_id"] = task_id
        
        # Update metrics
        if result["valid"]:
            metrics["successful_validations"] += 1
        else:
            metrics["failed_validations"] += 1
        
        # Update progress to 100%
        background_tasks_progress[task_id] = {"progress": 100, "message": "Validation complete", "result": result}
        await update_progress(task_id, 100, "Validation complete")
        
        # Schedule cleanup for any uploaded files
        if image_path and os.path.exists(image_path):
            asyncio.create_task(cleanup_file(image_path))
        if audio_path and os.path.exists(audio_path):
            asyncio.create_task(cleanup_file(audio_path))
            
    except Exception as e:
        logger.error(f"Error in background validation: {str(e)}")
        background_tasks_progress[task_id] = {"progress": -1, "message": f"Error: {str(e)}"}
        await update_progress(task_id, -1, f"Error: {str(e)}")

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to the Multimodal Validation API"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "up",
            "validators": {
                "multimodal": "up",
                "text": "up",
                "audio": "up",
                "clip": "up"
            }
        },
        "uptime": time.time() - metrics["start_time"]
    }
    
    return health_status

@app.get("/metrics")
async def get_metrics():
    """
    Performance metrics endpoint.
    """
    current_metrics = metrics.copy()
    current_metrics["uptime"] = time.time() - metrics["start_time"]
    current_metrics["timestamp"] = datetime.now().isoformat()
    
    return current_metrics

@app.get("/results/{request_id}")
async def get_result(request_id: str):
    """Retrieve a previously computed background validation result by request_id."""
    if request_id in background_tasks_progress:
        entry = background_tasks_progress[request_id]
        if "result" in entry:
            return entry["result"]
        return {"status": "in_progress", **entry}
    raise HTTPException(status_code=404, detail="Result not found")

@app.post("/validate/text", response_model=ValidationResponse)
async def validate_text(
    request: TextValidationRequest,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Validate text input.
    """
    try:
        start_time = time.time()
        
        # Auto-detect language if requested
        language = request.language
        try:
            if language.lower() == "auto":
                from langdetect import detect
                language = detect(request.text)
                # Map to supported set
                if language.startswith('en'):
                    language = 'en'
                elif language.startswith('si'):
                    language = 'si'
                elif language.startswith('ta'):
                    language = 'ta'
                else:
                    language = 'en'
        except Exception:
            language = request.language or 'en'

        # Validate text
        text_result = text_validator.validate_text(request.text, language)
        
        # Format response
        response = {
            "valid": text_result.get("valid", False),
            "confidence": text_result.get("confidence", 0.0),
            "confidence_interval": None,
            "routing": None,
            "modal_scores": {"text": text_result},
            "consistency": {},
            "feedback": {
                "suggestions": text_result.get("suggestions", []),
                "missing_elements": [],
                "message": text_result.get("message", "")
            },
            "processing_time": time.time() - start_time,
            "message": text_result.get("message", "")
        }
        
        # Update metrics
        metrics["requests"] += 1
        if response["valid"]:
            metrics["successful_validations"] += 1
        else:
            metrics["failed_validations"] += 1
        
        return response
        
    except Exception as e:
        logger.error(f"Error validating text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating text: {str(e)}"
        )

@app.post("/validate/voice", response_model=ValidationResponse)
async def validate_voice(
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Validate voice/audio input.
    """
    try:
        start_time = time.time()
        
        # Validate file type
        if not validate_file_type(audio_file, ALLOWED_AUDIO_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}. Supported types: {ALLOWED_AUDIO_TYPES}"
            )
        
        # Validate file size
        if not validate_file_size(audio_file, MAX_FILE_SIZE):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Save uploaded file
        audio_path = save_uploaded_file(audio_file)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, audio_path)
        
        # Validate audio
        audio_result = audio_validator.validate_audio(audio_path)
        
        # Format response
        response = {
            "valid": audio_result.get("valid", False),
            "confidence": audio_result.get("transcription", {}).get("confidence", 0.0),
            "confidence_interval": None,
            "routing": None,
            "modal_scores": {"audio": audio_result},
            "consistency": {},
            "feedback": {
                "suggestions": audio_result.get("recommendations", []),
                "missing_elements": [],
                "message": audio_result.get("message", "")
            },
            "processing_time": time.time() - start_time,
            "message": audio_result.get("message", "")
        }
        
        # Update metrics
        metrics["requests"] += 1
        if response["valid"]:
            metrics["successful_validations"] += 1
        else:
            metrics["failed_validations"] += 1
        
        return response
        
    except Exception as e:
        logger.error(f"Error validating audio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating audio: {str(e)}"
        )

@app.post("/validate/image", response_model=ValidationResponse)
async def validate_image(
    image_file: UploadFile = File(...),
    text: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Validate image input, optionally with text for CLIP-based alignment.
    """
    try:
        start_time = time.time()
        
        # Validate file type
        if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {image_file.content_type}. Supported types: {ALLOWED_IMAGE_TYPES}"
            )
        
        # Validate file size
        if not validate_file_size(image_file, MAX_FILE_SIZE):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Save uploaded file
        image_path = save_uploaded_file(image_file)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, image_path)
        
        # Validate image with full pipeline (blur, objects, privacy)
        image_result = image_validator.validate_image(image_path)
        
        # If text is provided, validate image-text alignment
        clip_result = {}
        if text:
            clip_result = clip_validator.validate_alignment(image_path, text)
        
        # Combine results
        combined_result = {**image_result}
        if clip_result:
            combined_result["alignment"] = clip_result
        
        # Format response
        response = {
            "valid": combined_result.get("valid", False),
            "confidence": combined_result.get("alignment", {}).get("alignment", {}).get("similarity", 0.0) if "alignment" in combined_result else (1.0 if combined_result.get("valid", False) else 0.0),
            "confidence_interval": None,
            "routing": None,
            "modal_scores": {"image": combined_result},
            "consistency": {},
            "feedback": {
                "suggestions": [],
                "missing_elements": [],
                "message": combined_result.get("message", "")
            },
            "processing_time": time.time() - start_time,
            "message": combined_result.get("message", "")
        }
        
        # Update metrics
        metrics["requests"] += 1
        if response["valid"]:
            metrics["successful_validations"] += 1
        else:
            metrics["failed_validations"] += 1
        
        return response
        
    except Exception as e:
        logger.error(f"Error validating image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating image: {str(e)}"
        )

@app.post("/validate/complete", response_model=ValidationResponse)
async def validate_complete(
    text: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    language: str = Form("en"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Perform complete multimodal validation with any combination of text, image, and audio inputs.
    """
    try:
        start_time = time.time()
        
        # Check if at least one modality is provided
        if text is None and image_file is None and audio_file is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one modality (text, image, or audio) must be provided"
            )
        
        # Process image if provided
        image_path = None
        if image_file:
            # Validate file type
            if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image file type: {image_file.content_type}. Supported types: {ALLOWED_IMAGE_TYPES}"
                )
            
            # Validate file size
            if not validate_file_size(image_file, MAX_FILE_SIZE):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image file too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024)}MB"
                )
            
            # Save uploaded file
            image_path = save_uploaded_file(image_file)
            
            # Schedule file cleanup
            background_tasks.add_task(cleanup_file, image_path)
        
        # Process audio if provided
        audio_path = None
        if audio_file:
            # Validate file type
            if not validate_file_type(audio_file, ALLOWED_AUDIO_TYPES):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported audio file type: {audio_file.content_type}. Supported types: {ALLOWED_AUDIO_TYPES}"
                )
            
            # Validate file size
            if not validate_file_size(audio_file, MAX_FILE_SIZE):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Audio file too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024)}MB"
                )
            
            # Save uploaded file
            audio_path = save_uploaded_file(audio_file)
            
            # Schedule file cleanup
            background_tasks.add_task(cleanup_file, audio_path)
        
        # Perform multimodal validation
        result = multimodal_validator.validate(text, image_path, audio_path, language)
        
        # Add request_id
        result["request_id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        
        # Update metrics
        metrics["requests"] += 1
        if result["valid"]:
            metrics["successful_validations"] += 1
        else:
            metrics["failed_validations"] += 1
        
        return result
        
    except Exception as e:
        logger.error(f"Error in complete validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in complete validation: {str(e)}"
        )

@app.websocket("/ws/validation/{client_id}")
async def websocket_validation(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time validation progress updates.
    """
    await websocket.accept()
    active_connections[client_id] = websocket
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({"status": "connected", "client_id": client_id})
        
        # Wait for messages
        while True:
            data = await websocket.receive_json()
            
            # Handle validation request
            if data.get("type") == "validate":
                task_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                
                # Process text validation
                text = data.get("text")
                image_path = None
                audio_path = None
                language = data.get("language", "en")
                
                # Start background task
                asyncio.create_task(process_validation_background(
                    task_id, text, image_path, audio_path, language
                ))
                
                # Send task ID to client
                await websocket.send_json({"task_id": task_id})
            
            # Handle task status request
            elif data.get("type") == "status" and "task_id" in data:
                task_id = data["task_id"]
                if task_id in background_tasks_progress:
                    await websocket.send_json({
                        "task_id": task_id,
                        **background_tasks_progress[task_id]
                    })
                else:
                    await websocket.send_json({
                        "task_id": task_id,
                        "progress": -1,
                        "message": "Task not found"
                    })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Remove connection from active connections
        if client_id in active_connections:
            del active_connections[client_id]

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for HTTP exceptions.
    """
    error_response = ErrorResponse(
        detail=str(exc.detail),
        status_code=exc.status_code,
        path=request.url.path
    )
    
    # Add suggestions based on error type
    if exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
        error_response.suggestion = f"Try uploading a smaller file (max {MAX_FILE_SIZE / (1024 * 1024)}MB)"
    elif exc.status_code == status.HTTP_400_BAD_REQUEST and "file type" in str(exc.detail).lower():
        error_response.suggestion = "Check the file format and try again with a supported format"
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        error_response.suggestion = "Please wait and try again later"
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler for unexpected errors.
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    
    error_response = ErrorResponse(
        detail="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        path=request.url.path,
        suggestion="Please try again later or contact support if the issue persists"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )

# Custom OpenAPI documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add API Key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": API_KEY_NAME
        }
    }
    
    # Apply security to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "security" not in operation:
                operation["security"] = [{"ApiKeyAuth": []}]
    
    # Add example requests and responses
    # Example for text validation
    text_path = openapi_schema["paths"]["/validate/text"]["post"]
    text_path["requestBody"]["content"]["application/json"]["example"] = {
        "text": "A silver watch with leather strap found near the park entrance",
        "language": "en"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Set custom OpenAPI schema
app.openapi = custom_openapi

# Serve static files (if available)
try:
    if os.path.isdir("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as _e:
    logger.warning(f"Static mount skipped: {_e}")

# Main entry point
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
