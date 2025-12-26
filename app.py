import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import time
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from functools import wraps
from datetime import datetime

import uvicorn
import asyncio
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import redis
from redis.exceptions import RedisError

# Initialize Redis client
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)
_redis_available = True

# Caching decorator
def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key_parts = [func.__name__]
            for arg in args:
                cache_key_parts.append(str(arg))
            for k, v in kwargs.items():
                cache_key_parts.append(f"{k}={v}")
            cache_key = ":".join(cache_key_parts)

            # Try to retrieve from cache
            global _redis_available
            cached_result = None
            if _redis_available:
                try:
                    cached_result = redis_client.get(cache_key)
                except RedisError as redis_error:
                    logger.warning(f"Redis unavailable, disabling cache (async path): {redis_error}")
                    _redis_available = False
            if cached_result:
                logger.info(f"Cache hit for {cache_key}")
                return json.loads(cached_result)

            # If not in cache, execute function and store result
            logger.info(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            if _redis_available:
                try:
                    redis_client.setex(cache_key, ttl, json.dumps(result))
                except RedisError as redis_error:
                    logger.warning(f"Redis unavailable while setting cache (async path): {redis_error}")
                    _redis_available = False
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key_parts = [func.__name__]
            for arg in args:
                cache_key_parts.append(str(arg))
            for k, v in kwargs.items():
                cache_key_parts.append(f"{k}={v}")
            cache_key = ":".join(cache_key_parts)

            # Try to retrieve from cache
            global _redis_available
            cached_result = None
            if _redis_available:
                try:
                    cached_result = redis_client.get(cache_key)
                except RedisError as redis_error:
                    logger.warning(f"Redis unavailable, disabling cache: {redis_error}")
                    _redis_available = False
            if cached_result:
                logger.info(f"Cache hit for {cache_key}")
                return json.loads(cached_result)

            # If not in cache, execute function and store result
            logger.info(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            if _redis_available:
                try:
                    redis_client.setex(cache_key, ttl, json.dumps(result))
                except RedisError as redis_error:
                    logger.warning(f"Redis unavailable while setting cache: {redis_error}")
                    _redis_available = False
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

import importlib
import importlib.util

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

# CORS configuration (explicit origins; wildcard + credentials is disallowed by browsers)
_default_cors = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3001,http://127.0.0.1:3001"
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_cors).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register research feature routers
try:
    from src.api.chat import router as chat_router
    from src.api.feedback import router as feedback_router
    
    app.include_router(chat_router)
    app.include_router(feedback_router)
    logger.info("✓ Research feature endpoints registered (Gemini chat + Active Learning)")
except Exception as e:
    logger.warning(f"Could not load research feature routers: {e}")

# File upload settings
UPLOAD_DIR = "uploads"
MAX_IMAGE_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_FILE_SIZE = 5 * 1024 * 1024   # 5MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_AUDIO_TYPES = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/m4a", "audio/webm"]

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Lazy validator initialization to allow server to boot without heavy deps
_consistency_engine = None
_text_validator = None
_voice_validator = None
_clip_validator = None
_image_validator = None
_database_manager = None

def get_text_validator():
    global _text_validator
    if _text_validator is None:
        try:
            mod = importlib.import_module('src.text.validator')
            _text_validator = mod.TextValidator(enable_logging=True)
        except Exception as e:
            logger.warning(f"Text validator unavailable: {e}")
            _text_validator = False
    return _text_validator or None

def get_voice_validator():
    global _voice_validator
    if _voice_validator is None:
        try:
            mod = importlib.import_module('src.voice.validator')
            _voice_validator = mod.VoiceValidator(enable_logging=True)
        except Exception as e:
            logger.warning(f"Voice validator unavailable: {e}")
            _voice_validator = False
    return _voice_validator or None

def get_image_validator():
    global _image_validator
    if _image_validator is None:
        try:
            mod = importlib.import_module('src.image.validator')
            _image_validator = mod.ImageValidator(enable_logging=True)
        except Exception as e:
            logger.warning(f"Image validator unavailable: {e}")
            _image_validator = False
    return _image_validator or None

def get_clip_validator():
    global _clip_validator
    if _clip_validator is None:
        try:
            mod = importlib.import_module('src.cross_modal.clip_validator')
            _clip_validator = mod.CLIPValidator(enable_logging=True)
        except Exception as e:
            logger.warning(f"CLIP validator unavailable: {e}")
            _clip_validator = False
    return _clip_validator or None

def get_consistency_engine():
    global _consistency_engine
    if _consistency_engine is None:
        try:
            mod = importlib.import_module('src.cross_modal.consistency_engine')
            _consistency_engine = mod.ConsistencyEngine()
        except Exception as e:
            logger.warning(f"Consistency engine unavailable: {e}")
            _consistency_engine = False
    return _consistency_engine or None


def get_database_manager():
    global _database_manager
    if _database_manager is None:
        if DatabaseManager is None:
            _database_manager = False
            return None
        try:
            _database_manager = DatabaseManager()
        except Exception as e:
            logger.warning(f"Database unavailable: {e}")
            _database_manager = False
    return _database_manager or None


def persist_validation_result(request_id: str, payload: Dict[str, Any]) -> None:
    """Persist validation results to the database when available."""
    db = get_database_manager()
    if not db:
        return
    db.save_validation_result(request_id, payload)

# Active WebSocket connections for progress updates
active_connections = {}

from src.monitoring.metrics_collector import MetricsCollector

try:
    from src.database import DatabaseManager
except ImportError:  # pragma: no cover
    DatabaseManager = None  # type: ignore

# Initialize MetricsCollector
metrics_collector = MetricsCollector()

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    # Start system metrics collection
    metrics_collector.start_system_metrics_collection()

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
        metrics_collector.request_counter.labels(endpoint=request.url.path, status=response.status_code).inc()
        metrics_collector.response_time_histogram.labels(endpoint=request.url.path).observe(process_time)
        
        return response

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Pydantic models for request/response validation
class ImageValidationResult(BaseModel):
    """Image validation result model"""
    image_path: str
    timestamp: str
    sharpness: dict
    objects: dict
    privacy: dict
    overall_score: float
    valid: bool

class TextValidationResult(BaseModel):
    """Text validation result model"""
    text: str
    timestamp: str
    completeness: dict
    coherence: dict
    entities: dict
    overall_score: float
    valid: bool
    clarification_questions: List[str] = []

class VoiceValidationResult(BaseModel):
    """Voice validation result model"""
    audio_path: str
    timestamp: str
    quality: dict
    transcription: dict
    valid: bool
    overall_score: float

class ValidationResponse(BaseModel):
    """Complete validation response model"""
    request_id: str
    timestamp: str
    input_types: List[str]
    image: Optional[ImageValidationResult] = None
    text: Optional[TextValidationResult] = None
    voice: Optional[VoiceValidationResult] = None
    cross_modal: dict
    confidence: dict
    feedback: dict
    clarification_questions: List[str] = []

class TextValidationRequest(BaseModel):
    text: str
    language: str = "en"  # use "auto" to enable language detection
    item_type_hint: Optional[str] = None
    color_hint: Optional[str] = None
    location_hint: Optional[str] = None

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

# ------------------------------------------------------------------ #
# Fallback and Graceful Degradation
# ------------------------------------------------------------------ #
async def validate_with_fallback(
    validator_func,
    *args,
    validator_name: str = "unknown",
    fallback_result: Optional[Dict] = None,
    **kwargs
) -> Dict:
    """
    Execute a validation with graceful fallback on failure.
    
    This implements progressive degradation where if a validator fails,
    we return a minimal result instead of crashing the entire request.
    This is especially important for:
    - ML model loading failures
    - Timeout scenarios
    - Resource exhaustion
    
    Args:
        validator_func: The validation function to call
        *args: Positional arguments for the validator
        validator_name: Name of the validator for logging
        fallback_result: Default result to return on failure
        **kwargs: Keyword arguments for the validator
        
    Returns:
        Validation result or fallback result on error
    """
    default_fallback = {
        "valid": False,
        "degraded": True,
        "error": None,
        "feedback": "Validation temporarily unavailable. Please try again.",
        "overall_score": 0.0
    }
    
    try:
        # Try to execute with a timeout to prevent hangs
        if asyncio.iscoroutinefunction(validator_func):
            result = await asyncio.wait_for(
                validator_func(*args, **kwargs),
                timeout=30.0  # 30 second timeout
            )
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: validator_func(*args, **kwargs)
            )
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"{validator_name} timed out after 30 seconds")
        fallback = fallback_result or default_fallback.copy()
        fallback["error"] = "Validation timed out. Try with a smaller file."
        fallback["degraded"] = True
        return fallback
        
    except Exception as e:
        logger.error(f"{validator_name} failed: {str(e)}")
        fallback = fallback_result or default_fallback.copy()
        fallback["error"] = str(e)
        fallback["degraded"] = True
        return fallback


def create_partial_result(
    image_result: Optional[Dict] = None,
    text_result: Optional[Dict] = None,
    voice_result: Optional[Dict] = None,
    cross_modal_results: Optional[Dict] = None
) -> Dict:
    """
    Create a partial validation result when some validators fail.
    
    This allows the system to return useful information even when
    not all validators are available, implementing the progressive
    degradation pattern.
    
    Args:
        image_result: Image validation result (or None if failed)
        text_result: Text validation result (or None if failed)
        voice_result: Voice validation result (or None if failed) cross_modal_results: Cross-modal results (or None if not computed)
        
    Returns:
        Dict with partial results and degradation info
    """
    available_modalities = []
    failed_modalities = []
    
    if image_result and not image_result.get("degraded"):
        available_modalities.append("image")
    elif image_result:
        failed_modalities.append("image")
        
    if text_result and not text_result.get("degraded"):
        available_modalities.append("text")
    elif text_result:
        failed_modalities.append("text")
        
    if voice_result and not voice_result.get("degraded"):
        available_modalities.append("voice")
    elif voice_result:
        failed_modalities.append("voice")
    
    # Calculate partial confidence based on available results
    scores = []
    if image_result and not image_result.get("degraded"):
        score = image_result.get("overall_score", 0)
        if score > 1:
            score = score / 100
        scores.append(score)
    if text_result and not text_result.get("degraded"):
        score = text_result.get("overall_score", 0)
        if score > 1:
            score = score / 100
        scores.append(score)
    if voice_result and not voice_result.get("degraded"):
        score = voice_result.get("overall_score", 0)
        if score > 1:
            score = score / 100  
        scores.append(score)
    
    partial_confidence = sum(scores) / len(scores) if scores else 0.0
    
    return {
        "partial": True,
        "available_modalities": available_modalities,
        "failed_modalities": failed_modalities,
        "partial_confidence": round(partial_confidence, 2),
        "can_proceed": len(available_modalities) >= 1,
        "recommendation": _get_degradation_recommendation(
            available_modalities, failed_modalities
        )
    }


def _get_degradation_recommendation(
    available: List[str], 
    failed: List[str]
) -> str:
    """Generate user-friendly recommendation based on what's available."""
    if not failed:
        return "All validations completed successfully."
    
    if not available:
        return (
            "All validators are currently unavailable. "
            "Please try again in a few minutes."
        )
    
    if len(available) >= 2:
        return (
            f"Partial validation completed using {', '.join(available)}. "
            f"Some checks ({', '.join(failed)}) were skipped due to temporary issues."
        )
    
    return (
        f"Limited validation available ({', '.join(available)} only). "
        f"For best results, please retry when all services are available."
    )


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

async def update_progress(client_id: str, progress: int, message: str, extra: Optional[Dict[str, Any]] = None):
    """
    Send progress updates to a WebSocket client.
    """
    if client_id in active_connections:
        websocket = active_connections[client_id]
        try:
            payload = {
                "progress": progress,
                "message": message
            }
            if extra:
                payload.update(extra)
            await websocket.send_json(payload)
        except Exception as e:
            logger.error(f"Error sending progress update: {str(e)}")

async def process_validation_background(client_id: str, task_id: str, text: Optional[str], image_path: Optional[str], audio_path: Optional[str], language: str):
    """
    Process validation in the background and update progress.
    """
    try:
        # Update progress to 10%
        background_tasks_progress[task_id] = {
            "client_id": client_id,
            "progress": 10,
            "message": "Starting validation"
        }
        await update_progress(client_id, 10, "Starting validation", {"task_id": task_id})
        
        # Initialize results
        text_result = None
        image_result = None
        voice_result = None
        clip_image_text_result = None
        voice_text_consistency_result = None
        
        input_types = []

        # Process text if provided
        if text:
            input_types.append("text")
            tv_bg = get_text_validator()
            if tv_bg is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Text validator unavailable on this instance")
            text_result = tv_bg.validate_text(text, language)
            await update_progress(client_id, 20, "Text validated", {"task_id": task_id})
        
        # Process image if provided
        if image_path:
            input_types.append("image")
            iv2 = get_image_validator()
            if iv2 is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Image validator unavailable on this instance")
            image_result = iv2.validate_image(image_path)
            # Inject missing fields for consistency
            image_result["image_path"] = image_path
            image_result["timestamp"] = datetime.now().isoformat()
            await update_progress(client_id, 40, "Image validated", {"task_id": task_id})
        
        # Process audio if provided
        if audio_path:
            input_types.append("voice")
            vv_bg = get_voice_validator()
            if vv_bg is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Voice validator unavailable on this instance")
            voice_result = vv_bg.validate_voice(audio_path)
            await update_progress(client_id, 60, "Voice validated", {"task_id": task_id})

        # Perform cross-modal consistency checks
        cross_modal_results = {}
        if image_path and text:
            cv_bg = get_clip_validator()
            if cv_bg is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="CLIP validator unavailable on this instance")
            clip_image_text_result = cv_bg.validate_image_text_alignment(image_path, text)
            cross_modal_results["image_text"] = clip_image_text_result
            await update_progress(client_id, 70, "Image-text consistency checked", {"task_id": task_id})
        
        if voice_result and text_result:
            ce_bg = get_consistency_engine()
            if ce_bg is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Consistency engine unavailable on this instance")
            voice_text_consistency_result = ce_bg.validate_voice_text_consistency(voice_result["transcription"]["transcription"], text)
            cross_modal_results["voice_text"] = voice_text_consistency_result
            context_consistency = ce_bg.validate_context_consistency(text_result, voice_result)
            cross_modal_results["context"] = context_consistency
            await update_progress(client_id, 80, "Voice-text consistency checked", {"task_id": task_id})

        # Calculate overall confidence
        ce_bg2 = get_consistency_engine()
        if ce_bg2 is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Consistency engine unavailable on this instance")
        confidence_results = ce_bg2.calculate_overall_confidence(
            image_result,
            text_result,
            voice_result,
            cross_modal_results
        )

        # Prepare feedback (simplified for now, can be expanded)
        feedback = {
            "suggestions": [],
            "missing_elements": [],
            "message": "Validation complete."
        }
        if not confidence_results["individual_scores"].get("image", 0) > 0 and "image" in input_types:
            feedback["suggestions"].append("Image quality could be improved.")
        if not confidence_results["individual_scores"].get("text", 0) > 0 and "text" in input_types:
            feedback["suggestions"].append("Text description could be more complete/coherent.")
        if not confidence_results["individual_scores"].get("voice", 0) > 0 and "voice" in input_types:
            feedback["suggestions"].append("Voice recording quality could be improved.")
        if not confidence_results["cross_modal_scores"].get("clip_similarity", 0) > 0 and "image" in input_types and "text" in input_types:
            feedback["suggestions"].append("Image and text description do not align well.")
        if not confidence_results["cross_modal_scores"].get("voice_text_similarity", 0) > 0 and "voice" in input_types and "text" in input_types:
            feedback["suggestions"].append("Voice and text description do not align well.")
        if cross_modal_results.get("context") and not cross_modal_results["context"].get("valid", True):
            feedback["suggestions"].append("Voice and text mention conflicting location or time details.")
        if cross_modal_results.get("context") and not cross_modal_results["context"].get("valid", True):
            feedback["suggestions"].append("Voice and text mention conflicting location or time details.")

        # Final response structure
        result = {
            "timestamp": datetime.now().isoformat(),
            "input_types": input_types,
            "image": image_result,
            "text": text_result,
            "voice": voice_result,
            "cross_modal": cross_modal_results,
            "confidence": confidence_results,
            "feedback": feedback
        }
        
        # Update progress to 90%
        background_tasks_progress[task_id] = {
            "client_id": client_id,
            "progress": 90,
            "message": "Finalizing results"
        }
        await update_progress(client_id, 90, "Finalizing results", {"task_id": task_id})
        
        # Add task_id to result
        result["request_id"] = task_id
        
        # Update metrics
        if confidence_results["overall_confidence"] >= 0.7:
            metrics_collector.record_validation_result("multimodal", confidence_results["overall_confidence"], confidence_results["routing"])
        else:
            metrics_collector.record_validation_failure("multimodal", "low_confidence")

        persist_validation_result(task_id, result)
        
        # Update progress to 100%
        background_tasks_progress[task_id] = {
            "client_id": client_id,
            "progress": 100,
            "message": "Validation complete",
            "result": result
        }
        await update_progress(client_id, 100, "Validation complete", {"task_id": task_id, "result": result})
        
        # Schedule cleanup for any uploaded files
        if image_path and os.path.exists(image_path):
            asyncio.create_task(cleanup_file(image_path))
        if audio_path and os.path.exists(audio_path):
            asyncio.create_task(cleanup_file(audio_path))
            
    except Exception as e:
        logger.error(f"Error in background validation: {str(e)}")
        background_tasks_progress[task_id] = {
            "client_id": client_id,
            "progress": -1,
            "message": f"Error: {str(e)}"
        }
        await update_progress(client_id, -1, f"Error: {str(e)}", {"task_id": task_id})

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
            "redis": "up" if redis_client.ping() else "down",
            "validators": {
                "image": "up" if importlib.util.find_spec('src.image.validator') else "down",
                "text": "up" if importlib.util.find_spec('src.text.validator') else "down",
                "voice": "up" if importlib.util.find_spec('src.voice.validator') else "down",
                "clip": "up" if importlib.util.find_spec('src.cross_modal.clip_validator') else "down",
                "consistency_engine": "up" if importlib.util.find_spec('src.cross_modal.consistency_engine') else "down"
            }
        },
        "uptime": time.time() - metrics_collector.start_time
    }
    
    return health_status

@app.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint.
    """
    # Prometheus client automatically exposes metrics at /metrics
    # This endpoint can be used for direct access or by Prometheus scraper
    return Response(content=generate_latest().decode("utf-8"), media_type="text/plain")

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
    start_time = time.time()
    
    # Auto-detect language if requested
    language = request.language or 'en'
    try:
        if language.lower() == "auto":
            from langdetect import detect
            detected = detect(request.text)
            if detected.startswith('en'):
                language = 'en'
            elif detected.startswith('si'):
                language = 'si'
            elif detected.startswith('ta'):
                language = 'ta'
            else:
                language = 'en'
    except Exception:
        # Fallback to provided or default language
        language = request.language or 'en'

    request_id = str(uuid.uuid4())

    # Validate text using lazy-initialized validator
    tv = get_text_validator()
    if tv is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Text validator unavailable on this instance")
    text_result = tv.validate_text(
        request.text,
        language,
        item_type_hint=request.item_type_hint,
        color_hint=request.color_hint,
        location_hint=request.location_hint
    )
    
    # Prepare response data
    response_data = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "input_types": ["text"],
        "text": text_result,
        "cross_modal": {},
        "confidence": {
            "overall_confidence": text_result["overall_score"],
            "routing": "high_quality" if text_result["valid"] else "low_quality",
            "action": "forward_to_matching" if text_result["valid"] else "return_for_improvement",
            "individual_scores": {"text": text_result["overall_score"]},
            "cross_modal_scores": {}
        },
        "feedback": {
            "suggestions": [],
            "missing_elements": text_result["completeness"].get("missing_info", []),
            "message": text_result.get("feedback", "") if isinstance(text_result.get("feedback"), str) else text_result.get("feedback", {}).get("message", "")
        },
        "clarification_questions": text_result.get("clarification_questions", [])
    }
    
    # Update metrics
    if text_result["valid"]:
        metrics_collector.record_validation_result("text", text_result["overall_score"], "high_quality")
    else:
        metrics_collector.record_validation_failure("text", "invalid")
    
    persist_validation_result(request_id, response_data)
    return ValidationResponse(**response_data)

@app.post("/validate/voice", response_model=ValidationResponse)
async def validate_voice(
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: APIKey = Depends(get_api_key)
):
    """
    Validate voice/audio input.
    """
    start_time = time.time()
    
    request_id = str(uuid.uuid4())

    try:
        # Validate file type
        if not validate_file_type(audio_file, ALLOWED_AUDIO_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}. Supported types: {ALLOWED_AUDIO_TYPES}"
            )
        
        # Validate file size
        if not validate_file_size(audio_file, MAX_AUDIO_FILE_SIZE):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_AUDIO_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Save uploaded file
        audio_path = save_uploaded_file(audio_file)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, audio_path)
        
        # Validate audio
        vv = get_voice_validator()
        if vv is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Voice validator unavailable on this instance")
        voice_result = cached()(vv.validate_voice)(audio_path)
        
        # Prepare response data
        response_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "input_types": ["voice"],
            "voice": voice_result,
            "cross_modal": {},
            "confidence": {
                "overall_confidence": voice_result["overall_score"],
                "routing": "high_quality" if voice_result["valid"] else "low_quality",
                "action": "forward_to_matching" if voice_result["valid"] else "return_for_improvement",
                "individual_scores": {"voice": voice_result["overall_score"]},
                "cross_modal_scores": {}
            },
            "feedback": {
                "suggestions": [],
                "missing_elements": [],
                "message": voice_result["quality"].get("feedback", "")
            }
        }
        
        # Update metrics
        if voice_result["valid"]:
            metrics_collector.record_validation_result("voice", voice_result["overall_score"], "high_quality")
        else:
            metrics_collector.record_validation_failure("voice", "invalid")
        
        persist_validation_result(request_id, response_data)
        return ValidationResponse(**response_data)
        
    except HTTPException:
        raise # Re-raise HTTPException to be handled by FastAPI's exception handler
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
    start_time = time.time()
    
    request_id = str(uuid.uuid4())

    try:
        # Validate file type
        if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {image_file.content_type}. Supported types: {ALLOWED_IMAGE_TYPES}"
            )
        
        # Validate file size
        if not validate_file_size(image_file, MAX_IMAGE_FILE_SIZE):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_IMAGE_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Save uploaded file
        image_path = save_uploaded_file(image_file)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_file, image_path)
        
        # Validate image with full pipeline (blur, objects, privacy)
        iv = get_image_validator()
        if iv is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Image validator unavailable on this instance")
        image_result = cached()(iv.validate_image)(image_path, text)
        
        # Inject missing fields required by ImageValidationResult model
        image_result["image_path"] = image_path
        image_result["timestamp"] = datetime.now().isoformat()
        
        # If text is provided, validate image-text alignment
        clip_image_text_result = None
        if text:
            cv = get_clip_validator()
            if cv is not None:
                clip_image_text_result = cached()(cv.validate_image_text_alignment)(image_path, text)
        
        # Prepare response data
        response_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "input_types": ["image"] + (["text"] if text else []),
            "image": image_result,
            "text": None, # Not directly validated in this endpoint
            "voice": None, # Not directly validated in this endpoint
            "cross_modal": {"image_text": clip_image_text_result} if clip_image_text_result else {},
            "confidence": {
                "overall_confidence": image_result["overall_score"],
                "routing": "high_quality" if image_result["valid"] else "low_quality",
                "action": "forward_to_matching" if image_result["valid"] else "return_for_improvement",
                "individual_scores": {"image": image_result["overall_score"]},
                "cross_modal_scores": {"clip_similarity": clip_image_text_result["similarity"]} if clip_image_text_result else {}
            },
            "feedback": {
                "suggestions": [],
                "missing_elements": [],
                "message": image_result["sharpness"].get("feedback", "") + ". " + image_result["objects"].get("feedback", "")
            }
        }
        
        # Update metrics
        if image_result["valid"]:
            metrics_collector.record_validation_result("image", image_result["overall_score"], "high_quality")
        else:
            metrics_collector.record_validation_failure("image", "invalid")
        
        persist_validation_result(request_id, response_data)
        return ValidationResponse(**response_data)
        
    except HTTPException:
        raise # Re-raise HTTPException to be handled by FastAPI's exception handler
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
    start_time = time.time()
    
    # Initialize results
    text_result = None
    image_result = None
    voice_result = None
    clip_image_text_result = None
    voice_text_consistency_result = None
    
    input_types = []

    request_id = str(uuid.uuid4())

    try:
        # Check if at least one modality is provided
        if text is None and image_file is None and audio_file is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one modality (text, image, or audio) must be provided"
            )
        
        # Process text if provided
        if text:
            input_types.append("text")
            tv = get_text_validator()
            if tv is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Text validator unavailable on this instance")
            text_result = tv.validate_text(text, language)
        
        # Process image if provided
        image_path = None
        if image_file:
            input_types.append("image")
            # Validate file type
            if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image file type: {image_file.content_type}. Supported types: {ALLOWED_IMAGE_TYPES}"
                )
            
            # Validate file size
            if not validate_file_size(image_file, MAX_IMAGE_FILE_SIZE):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image file too large. Maximum size: {MAX_IMAGE_FILE_SIZE / (1024 * 1024)}MB"
                )
            
            # Save uploaded file
            image_path = save_uploaded_file(image_file)
            
            # Schedule file cleanup
            background_tasks.add_task(cleanup_file, image_path)
            
            iv = get_image_validator()
            if iv is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Image validator unavailable on this instance")
            image_result = iv.validate_image(image_path)
            # Inject missing fields required by ImageValidationResult model
            image_result["image_path"] = image_path
            image_result["timestamp"] = datetime.now().isoformat()
        
        # Process audio if provided
        audio_path = None
        if audio_file:
            input_types.append("voice")
            # Validate file type
            if not validate_file_type(audio_file, ALLOWED_AUDIO_TYPES):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported audio file type: {audio_file.content_type}. Supported types: {ALLOWED_AUDIO_TYPES}"
                )
            
            # Validate file size
            if not validate_file_size(audio_file, MAX_AUDIO_FILE_SIZE):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Audio file too large. Maximum size: {MAX_AUDIO_FILE_SIZE / (1024 * 1024)}MB"
                )
            
            # Save uploaded file
            audio_path = save_uploaded_file(audio_file)
            
            # Schedule file cleanup
            background_tasks.add_task(cleanup_file, audio_path)
            
            vv = get_voice_validator()
            if vv is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Voice validator unavailable on this instance")
            voice_result = vv.validate_voice(audio_path)

        # Perform cross-modal consistency checks
        cross_modal_results = {}
        if image_path and text:
            cv = get_clip_validator()
            if cv is not None:
                clip_image_text_result = cached()(cv.validate_image_text_alignment)(image_path, text)
            cross_modal_results["image_text"] = clip_image_text_result
        
        if voice_result and text_result:
            ce = get_consistency_engine()
            if ce is None:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Consistency engine unavailable on this instance")
            voice_text_consistency_result = cached()(ce.validate_voice_text_consistency)(
                voice_result["transcription"]["transcription"], text
            )
            cross_modal_results["voice_text"] = voice_text_consistency_result
            context_consistency = cached()(ce.validate_context_consistency)(text_result, voice_result)
            cross_modal_results["context"] = context_consistency
        
        # Calculate overall confidence
        ce2 = get_consistency_engine()
        if ce2 is None:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Consistency engine unavailable on this instance")
        confidence_results = ce2.calculate_overall_confidence(
            image_result,
            text_result,
            voice_result,
            cross_modal_results
        )

        # Prepare feedback (simplified for now, can be expanded)
        feedback = {
            "suggestions": [],
            "missing_elements": [],
            "message": "Validation complete."
        }
        if not confidence_results["individual_scores"].get("image", 0) > 0 and "image" in input_types:
            feedback["suggestions"].append("Image quality could be improved.")
        if not confidence_results["individual_scores"].get("text", 0) > 0 and "text" in input_types:
            feedback["suggestions"].append("Text description could be more complete/coherent.")
        if not confidence_results["individual_scores"].get("voice", 0) > 0 and "voice" in input_types:
            feedback["suggestions"].append("Voice recording quality could be improved.")
        if not confidence_results["cross_modal_scores"].get("clip_similarity", 0) > 0 and "image" in input_types and "text" in input_types:
            feedback["suggestions"].append("Image and text description do not align well.")
        if not confidence_results["cross_modal_scores"].get("voice_text_similarity", 0) > 0 and "voice" in input_types and "text" in input_types:
            feedback["suggestions"].append("Voice and text description do not align well.")

        # Final response structure
        response_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "input_types": input_types,
            "image": image_result,
            "text": text_result,
            "voice": voice_result,
            "cross_modal": cross_modal_results,
            "confidence": confidence_results,
            "feedback": feedback
        }
        
        # Update metrics
        if confidence_results["overall_confidence"] >= 0.7:
            metrics_collector.record_validation_result("multimodal", confidence_results["overall_confidence"], confidence_results["routing"])
        else:
            metrics_collector.record_validation_failure("multimodal", "low_confidence")
        
        persist_validation_result(request_id, response_data)
        return ValidationResponse(**response_data)
        
    except HTTPException:
        raise # Re-raise HTTPException to be handled by FastAPI's exception handler
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
                image_path = data.get("image_path")
                audio_path = data.get("audio_path")
                language = data.get("language", "en")
                
                # Start background task
                asyncio.create_task(process_validation_background(
                    client_id, task_id, text, image_path, audio_path, language
                ))
                
                # Send task ID to client
                await websocket.send_json({"task_id": task_id, "status": "accepted"})
            
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
        error_response.suggestion = f"Try uploading a smaller file (max {MAX_IMAGE_FILE_SIZE / (1024 * 1024)}MB)"
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
    text_path["responses"]["200"]["content"]["application/json"]["example"] = {
        "timestamp": "2023-10-27T10:00:00.000000",
        "input_types": ["text"],
        "image": None,
        "text": {
            "text": "A silver watch with leather strap found near the park entrance",
            "timestamp": "2023-10-27 10:00:00",
            "completeness": {
                "valid": True,
                "score": 1.0,
                "entities": {"item_type": ["watch"], "color": ["silver"], "location": ["park entrance"]},
                "missing_info": [],
                "feedback": "Description contains all required elements"
            },
            "coherence": {
                "valid": True,
                "score": 0.9,
                "feedback": "Description is semantically coherent"
            },
            "entities": {
                "entities": [
                    {"text": "silver watch", "label": "PRODUCT", "start": 2, "end": 14},
                    {"text": "park entrance", "label": "LOC", "start": 36, "end": 49}
                ],
                "item_mentions": ["watch"],
                "color_mentions": ["silver"],
                "location_mentions": ["park entrance"]
            },
            "overall_score": 0.95,
            "valid": True
        },
        "voice": None,
        "cross_modal": {},
        "confidence": {
            "overall_confidence": 0.95,
            "routing": "high_quality",
            "action": "forward_to_matching",
            "individual_scores": {"text": 0.95},
            "cross_modal_scores": {}
        },
        "feedback": {
            "suggestions": [],
            "missing_elements": [],
            "message": "Description contains all required elements. Description is semantically coherent"
        }
    }

    # Example for image validation
    image_path = openapi_schema["paths"]["/validate/image"]["post"]
    image_path["requestBody"]["content"]["multipart/form-data"]["example"] = {
        "image_file": "<binary file>",
        "text": "A red iPhone"
    }
    image_path["responses"]["200"]["content"]["application/json"]["example"] = {
        "timestamp": "2023-10-27T10:00:00.000000",
        "input_types": ["image", "text"],
        "image": {
            "image_path": "uploads/20231027100000000000_test_image.jpg",
            "timestamp": "2023-10-27 10:00:00",
            "sharpness": {"valid": True, "score": 150.0, "threshold": 100.0, "feedback": "Image is sharp"},
            "objects": {"valid": True, "detections": [{"class": "phone", "confidence": 0.95, "bbox": [10, 10, 50, 50]}], "feedback": "Detected 1 objects"},
            "privacy": {"faces_detected": 0, "privacy_protected": False, "processed_image": None, "feedback": "No faces detected"},
            "overall_score": 0.9,
            "valid": True
        },
        "text": None,
        "voice": None,
        "cross_modal": {
            "image_text": {"valid": True, "similarity": 0.92, "threshold": 0.85, "feedback": "Image and text are semantically aligned"}
        },
        "confidence": {
            "overall_confidence": 0.91,
            "routing": "high_quality",
            "action": "forward_to_matching",
            "individual_scores": {"image": 0.9},
            "cross_modal_scores": {"clip_similarity": 0.92}
        },
        "feedback": {
            "suggestions": [],
            "missing_elements": [],
            "message": "Image is sharp. Detected 1 objects"
        }
    }

    # Example for voice validation
    voice_path = openapi_schema["paths"]["/validate/voice"]["post"]
    voice_path["requestBody"]["content"]["multipart/form-data"]["example"] = {
        "audio_file": "<binary file>"
    }
    voice_path["responses"]["200"]["content"]["application/json"]["example"] = {
        "timestamp": "2023-10-27T10:00:00.000000",
        "input_types": ["voice"],
        "image": None,
        "text": None,
        "voice": {
            "audio_path": "uploads/20231027100000000000_test_audio.wav",
            "timestamp": "2023-10-27 10:00:00",
            "quality": {"valid": True, "duration": 15.2, "snr": 28.5, "duration_valid": True, "quality_valid": True, "feedback": "Audio quality assessment passed"},
            "transcription": {"valid": True, "transcription": "I lost my keys in the cafeteria", "confidence": 0.91, "language": "en", "feedback": "Speech recognition successful"},
            "overall_score": 0.88,
            "valid": True
        },
        "cross_modal": {},
        "confidence": {
            "overall_confidence": 0.88,
            "routing": "high_quality",
            "action": "forward_to_matching",
            "individual_scores": {"voice": 0.88},
            "cross_modal_scores": {}
        },
        "feedback": {
            "suggestions": [],
            "missing_elements": [],
            "message": "Audio quality assessment passed. Speech recognition successful"
        }
    }

    # Example for complete validation
    complete_path = openapi_schema["paths"]["/validate/complete"]["post"]
    complete_path["requestBody"]["content"]["multipart/form-data"]["example"] = {
        "text": "Lost my red iPhone 13 in the library yesterday afternoon",
        "image_file": "<binary file>",
        "audio_file": "<binary file>"
    }
    complete_path["responses"]["200"]["content"]["application/json"]["example"] = {
        "timestamp": "2023-10-27T10:00:00.000000",
        "input_types": ["text", "image", "voice"],
        "image": {
            "image_path": "uploads/20231027100000000000_test_image.jpg",
            "timestamp": "2023-10-27 10:00:00",
            "sharpness": {"valid": True, "score": 150.0, "threshold": 100.0, "feedback": "Image is sharp"},
            "objects": {"valid": True, "detections": [{"class": "phone", "confidence": 0.95, "bbox": [10, 10, 50, 50]}], "feedback": "Detected 1 objects"},
            "privacy": {"faces_detected": 0, "privacy_protected": False, "processed_image": None, "feedback": "No faces detected"},
            "overall_score": 0.9,
            "valid": True
        },
        "text": {
            "text": "Lost my red iPhone 13 in the library yesterday afternoon",
            "timestamp": "2023-10-27 10:00:00",
            "completeness": {"valid": True, "score": 1.0, "entities": {"item_type": ["iphone"], "color": ["red"], "location": ["library"]}, "missing_info": [], "feedback": "Description contains all required elements"},
            "coherence": {"valid": True, "score": 0.9, "feedback": "Description is semantically coherent"},
            "entities": {"entities": [], "item_mentions": ["iphone"], "color_mentions": ["red"], "location_mentions": ["library"]},
            "overall_score": 0.95,
            "valid": True
        },
        "voice": {
            "audio_path": "uploads/20231027100000000000_test_audio.wav",
            "timestamp": "2023-10-27 10:00:00",
            "quality": {"valid": True, "duration": 15.2, "snr": 28.5, "duration_valid": True, "quality_valid": True, "feedback": "Audio quality assessment passed"},
            "transcription": {"valid": True, "transcription": "I lost my red iPhone 13 in the library", "confidence": 0.91, "language": "en", "feedback": "Speech recognition successful"},
            "overall_score": 0.88,
            "valid": True
        },
        "cross_modal": {
            "image_text": {"valid": True, "similarity": 0.92, "threshold": 0.85, "feedback": "Image and text are semantically aligned"},
            "voice_text": {"valid": True, "similarity": 0.88, "threshold": 0.75, "feedback": "Voice and text are semantically consistent"}
        },
        "confidence": {
            "overall_confidence": 0.9,
            "routing": "high_quality",
            "action": "forward_to_matching",
            "individual_scores": {"image": 0.9, "text": 0.95, "voice": 0.88},
            "cross_modal_scores": {"clip_similarity": 0.92, "voice_text_similarity": 0.88}
        },
        "feedback": {
            "suggestions": [],
            "missing_elements": [],
            "message": "Validation complete."
        }
    }

# Set custom OpenAPI schema
app.openapi = custom_openapi

# Serve static files (if available)
try:
    if os.path.isdir("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as _e:
    logger.warning(f"Static mount skipped: {_e}")

# ------------------------------------------------------------------ #
# Active Learning Feedback Endpoint
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# Active Learning Feedback Endpoint
# ------------------------------------------------------------------ #
class FeedbackRequest(BaseModel):
    request_id: str
    modality: str
    predicted_label: Optional[str] = None
    user_correction: Optional[str] = None
    is_correct: bool
    comments: Optional[str] = None

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest, x_api_key: str = Header(None)):
    """
    Submit user feedback for Active Learning.
    Stores corrections for low-confidence predictions to improve future models.
    """
    # Verify API Key
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
        
    try:
        # Store in database
        query = db_manager.feedback_logs.insert().values(
            request_id=feedback.request_id,
            modality=feedback.modality,
            predicted_label=feedback.predicted_label,
            user_correction=feedback.user_correction,
            is_correct=feedback.is_correct,
            comments=feedback.comments,
            timestamp=datetime.now()
        )
        
        with db_manager.engine.connect() as conn:
            conn.execute(query)
            conn.commit()
            
        logger.info(f"Feedback received for request {feedback.request_id}: Correct={feedback.is_correct}")
        
        return {
            "status": "success", 
            "message": "Feedback stored for active learning",
            "active_learning_triggered": not feedback.is_correct # Retraining candidate if wrong
        }
        
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store feedback: {str(e)}"
        )
    request_id: str
    modality: str
    predicted_label: Optional[str] = None
    user_correction: Optional[str] = None
    is_correct: bool
    comments: Optional[str] = None

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest, x_api_key: str = Header(None)):
    """
    Submit user feedback for Active Learning.
    Stores corrections for low-confidence predictions to improve future models.
    """
    # Verify API Key
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
        
    try:
        # Store in database
        query = db_manager.feedback_logs.insert().values(
            request_id=feedback.request_id,
            modality=feedback.modality,
            predicted_label=feedback.predicted_label,
            user_correction=feedback.user_correction,
            is_correct=feedback.is_correct,
            comments=feedback.comments,
            timestamp=datetime.now()
        )
        
        with db_manager.engine.connect() as conn:
            conn.execute(query)
            conn.commit()
            
        logger.info(f"Feedback received for request {feedback.request_id}: Correct={feedback.is_correct}")
        
        return {
            "status": "success", 
            "message": "Feedback stored for active learning",
            "active_learning_triggered": not feedback.is_correct # Retraining candidate if wrong
        }
        
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store feedback: {str(e)}"
        )

# Main entry point
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
