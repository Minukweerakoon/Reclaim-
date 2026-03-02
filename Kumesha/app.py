import os
import sys

# Ensure the root directory is in the PYTHONPATH to resolve 'src' imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import time
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from functools import wraps
from datetime import datetime, timedelta

import uvicorn
import asyncio
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, status, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.responses import JSONResponse, Response, FileResponse
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

# API key dependency shared across routers/endpoints
from src.api.auth import API_KEY_NAME, api_key_header, get_api_key

# Rate limiting settings
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # requests per window
rate_limit_storage = {}  # IP -> {count: int, reset_time: float}

# CORS configuration (explicit origins; wildcard + credentials is disallowed by browsers)
_default_cors = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3001,http://127.0.0.1:3001,http://localhost:8000,http://127.0.0.1:8000"
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

# Firebase-backed reports API
try:
    from src.api.reports import router as reports_router
    app.include_router(reports_router)
    logger.info("✓ Reports API registered (Firebase Firestore)")
except Exception as e:
    logger.warning(f"Could not load reports router: {e}")

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
            logger.info("[DEBUG] Attempting to import src.cross_modal.clip_validator")
            mod = importlib.import_module('src.cross_modal.clip_validator')
            logger.info(f"[DEBUG] Successfully imported module: {mod}")
            _clip_validator = mod.CLIPValidator(enable_logging=True)
            logger.info(f"[DEBUG] Successfully initialized CLIPValidator: {_clip_validator}")
        except Exception as e:
            import traceback
            logger.warning(f"CLIP validator unavailable: {e}")
            logger.error(f"[DEBUG] Full traceback:\n{traceback.format_exc()}")
            _clip_validator = False
    return _clip_validator or None

def get_consistency_engine():
    global _consistency_engine
    if _consistency_engine is None:
        try:
            import importlib
            import sys
            # Force fresh import by removing cached module
            module_name = 'src.cross_modal.consistency_engine'
            if module_name in sys.modules:
                del sys.modules[module_name]
            mod = importlib.import_module(module_name)
            _consistency_engine = mod.ConsistencyEngine()
            logger.info(f"ConsistencyEngine initialized: {_consistency_engine}")
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
    supabase_id: Optional[str] = None
    image_url: Optional[str] = None

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

# Novel Feature #1: Spatial-Temporal Context Validation Models
class SpatialTemporalRequest(BaseModel):
    """Request model for spatial-temporal context validation"""
    item_type: str = Field(..., description="Type of item (e.g., 'laptop', 'phone', 'wallet')")
    location: str = Field(..., description="Where the item was lost/found")
    time: Optional[str] = Field(None, description="When the item was lost/found (e.g., '2pm', 'morning')")

class SpatialTemporalResponse(BaseModel):
    """Response model for spatial-temporal context validation"""
    plausibility_score: float = Field(..., description="Score from 0.0 to 1.0")
    valid: bool = Field(..., description="True if plausibility >= 0.4")
    location_probability: float
    time_probability: Optional[float] = None  # None when time is not provided
    explanation: str
    suggestions: List[str] = []
    confidence_level: str
    normalized_inputs: dict

# Phase 2: XAI Attention Visualization Models
class AttentionMapRequest(BaseModel):
    """Request model for generating attention heatmaps"""
    text: str = Field(..., description="Text description to match with image")

class AttentionMapResponse(BaseModel):
    """Response model for attention heatmap generation"""
    heatmap_url: Optional[str] = Field(None, description="URL to generated heatmap image")
    attention_scores: List[float] = Field(default_factory=list, description="Raw attention weights")
    top_regions: List[Dict[str, Any]] = Field(default_factory=list, description="Most attended regions")
    explanation: str = Field("", description="Human-readable explanation")
    error: Optional[str] = None

class EnhancedXAIRequest(BaseModel):
    """Request for comprehensive XAI explanation"""
    include_attention: bool = Field(False, description="Include attention analysis")
    include_discrepancies: bool = Field(True, description="Include multi-dimensional discrepancy checks")


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


@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    """
    # Check Redis status safely
    redis_status = "down"
    try:
        if redis_client.ping():
            redis_status = "up"
    except Exception:
        redis_status = "down"

    # Build uptime safely
    try:
        uptime = time.time() - metrics_collector.start_time
    except Exception:
        uptime = 0

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "up",
            "redis": redis_status,
            "validators": {
                "image": "up" if importlib.util.find_spec('src.image.validator') else "down",
                "text": "up" if importlib.util.find_spec('src.text.validator') else "down",
                "voice": "up" if importlib.util.find_spec('src.voice.validator') else "down",
                "clip": "up" if importlib.util.find_spec('src.cross_modal.clip_validator') else "down",
                "consistency_engine": "up" if importlib.util.find_spec('src.cross_modal.consistency_engine') else "down"
            }
        },
        "uptime": uptime
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

# NOTE: GET /api/reports is handled by the Firebase-backed reports router
# (src/api/reports.py). The Monitor dashboard uses GET /api/reports/all
# which lists all reports without per-user Firebase auth.

# ------------------------------------------------------------------ #
# Novel Feature #1: Spatial-Temporal Context Validation
# Research Contribution: Bayesian Probabilistic Plausibility Assessment
# ------------------------------------------------------------------ #
@app.post("/api/validate/context", response_model=SpatialTemporalResponse)
async def validate_spatial_temporal_context(
    request: SpatialTemporalRequest,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Validate the plausibility of an item-location-time combination.
    
    This implements Novel Feature #1: Bayesian Probabilistic Spatial-Temporal
    Context Validation for A-Grade research publication.
    
    Mathematical Model:
        Plausibility = P(Location|Item) × P(Time|Item)
    
    Examples:
        - "laptop" + "library" + "2pm" → 0.85 (Very Plausible)
        - "swimsuit" + "server room" + "9am" → 0.02 (Highly Implausible)
    
    Returns:
        SpatialTemporalResponse with plausibility score and explanation
    """
    try:
        from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator
        validator = get_spatial_temporal_validator()
        
        result = validator.calculate_plausibility(
            item=request.item_type,
            location=request.location,
            time=request.time
        )
        
        # Log for research metrics
        logger.info(
            f"Spatial-Temporal Validation: {request.item_type} @ {request.location} "
            f"({request.time}) → Score: {result['plausibility_score']}"
        )
        
        return SpatialTemporalResponse(**result)
        
    except Exception as e:
        logger.error(f"Spatial-temporal validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial-temporal validation failed: {str(e)}"
        )

@app.get("/api/spatial-temporal/stats")
async def get_spatial_temporal_stats(api_key: APIKey = Depends(get_api_key)):
    """
    Get statistics about the spatial-temporal validation system.
    Shows learned patterns and prior data status.
    """
    try:
        from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator
        validator = get_spatial_temporal_validator()
        
        return {
            "status": "operational",
            "learning_stats": validator.get_learning_stats(),
            "sample_validations": [
                validator.calculate_plausibility("laptop", "library", "2pm"),
                validator.calculate_plausibility("phone", "cafeteria", "noon"),
                validator.calculate_plausibility("swimsuit", "server room", "9am"),
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get spatial-temporal stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ================================================================
# Phase 3: Advanced Entity Detection Endpoints
# ================================================================

@app.post("/api/entities/detect/text")
async def detect_text_entities(
    request: TextValidationRequest,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Extract entities (item_type, color, location, brand, time) from text using the TextValidator.
    Used by the frontend Spatial-Temporal Context analysis.
    """
    try:
        tv = get_text_validator()
        if tv is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Text validator unavailable on this instance"
            )
        entity_result = tv.extract_entities(request.text, request.language or 'en')

        # extract_entities returns:
        #   entities: list of {text, label, start, end}  (spaCy NER)
        #   item_mentions, color_mentions, location_mentions, brand_mentions, style_mentions
        raw_entities = entity_result.get("entities", [])
        return {
            "entities": {
                "item_type": entity_result.get("item_mentions", []),
                "color": entity_result.get("color_mentions", []),
                "brand": entity_result.get("brand_mentions", []),
                "location": entity_result.get("location_mentions", []),
                "time": [e["text"] for e in raw_entities if e.get("label") in ("DATE", "TIME")],
            },
            "raw_entities": raw_entities,
            "confidence": 0.8 if entity_result.get("item_mentions") else 0.4,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text entity detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text entity detection failed: {str(e)}"
        )

@app.post("/api/entities/detect")
async def detect_advanced_entities(
    image_file: UploadFile = File(...),
    text: Optional[str] = Form(None),
    detect_brand: bool = Form(True),
    detect_material: bool = Form(True),
    detect_size: bool = Form(True),
    detect_ocr: bool = Form(True),
    detect_condition: bool = Form(True),
    api_key: APIKey = Depends(get_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Advanced entity detection endpoint.
    
    Detects:
    - Brand/Logo (CLIP zero-shot)
    - Material (leather, metal, plastic, etc.)
    - Size category (small, medium, large)
    - OCR text and serial numbers
    - Condition (new, used, good)
    
    Args:
        image_file: Image to analyze
        text: Optional text description for context
        detect_*: Flags to enable/disable specific detections
    """
    start_time = time.time()
    
    try:
        # Validate image
        if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image type: {image_file.content_type}"
            )
        
        # Save uploaded file
        image_path = save_uploaded_file(image_file)
        background_tasks.add_task(cleanup_file, image_path)
        
        # Import detector
        from src.cross_modal.advanced_entity_detector import (
            detect_brand_logo,
            detect_material,
            estimate_size,
            extract_text_ocr,
            get_custom_entity_detector
        )
        
        results = {
            "image_path": image_path,
            "text_hint": text,
            "detections": {}
        }
        
        # Run requested detections
        if detect_brand:
            try:
                results["detections"]["brand"] = detect_brand_logo(image_path)
            except Exception as e:
                results["detections"]["brand"] = {"error": str(e)}
        
        if detect_material:
            try:
                results["detections"]["material"] = detect_material(image_path)
            except Exception as e:
                results["detections"]["material"] = {"error": str(e)}
        
        if detect_size:
            try:
                results["detections"]["size"] = estimate_size(image_path)
            except Exception as e:
                results["detections"]["size"] = {"error": str(e)}
        
        if detect_ocr:
            try:
                results["detections"]["ocr"] = extract_text_ocr(image_path)
            except Exception as e:
                results["detections"]["ocr"] = {"error": str(e)}
        
        if detect_condition:
            try:
                detector = get_custom_entity_detector()
                results["detections"]["condition"] = detector.detect(image_path, "condition")
            except Exception as e:
                results["detections"]["condition"] = {"error": str(e)}
        
        results["processing_time"] = round(time.time() - start_time, 3)
        
        logger.info(f"Advanced entity detection complete in {results['processing_time']}s")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced entity detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Entity detection failed: {str(e)}"
        )


@app.get("/api/entities/types")
async def list_entity_types(api_key: APIKey = Depends(get_api_key)):
    """
    List available entity detection types and custom entities.
    """
    try:
        from src.cross_modal.advanced_entity_detector import (
            KNOWN_BRANDS, MATERIALS, SIZE_CATEGORIES, get_custom_entity_detector
        )
        
        detector = get_custom_entity_detector()
        
        return {
            "built_in_detections": {
                "brand": {
                    "description": "Detect brand logos using CLIP",
                    "supported_brands": KNOWN_BRANDS[:20],  # Sample
                    "total_brands": len(KNOWN_BRANDS)
                },
                "material": {
                    "description": "Detect material type",
                    "supported_materials": MATERIALS
                },
                "size": {
                    "description": "Estimate relative size category",
                    "categories": [cat for cat, _ in SIZE_CATEGORIES]
                },
                "ocr": {
                    "description": "Extract text and serial numbers from image",
                    "features": ["text_extraction", "serial_number_detection"]
                }
            },
            "custom_entities": detector.list_entities()
        }
    except Exception as e:
        logger.error(f"Failed to list entity types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ================================================================
# Phase 2: XAI Attention Visualization Endpoints
# ================================================================

@app.post("/api/xai/attention", response_model=AttentionMapResponse)
async def generate_attention_heatmap(
    image_file: UploadFile = File(...),
    text: str = Form(...),
    api_key: APIKey = Depends(get_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate attention heatmap for image-text pair.
    Shows which image regions the model focuses on when matching text.
    
    Phase 2: XAI Attention Visualization
    """
    try:
        from src.cross_modal.attention_visualizer import get_attention_visualizer
        
        # Validate and save image
        if not validate_file_type(image_file, ALLOWED_IMAGE_TYPES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image type. Allowed: {ALLOWED_IMAGE_TYPES}"
            )
        
        image_path = save_uploaded_file(image_file)
        background_tasks.add_task(cleanup_file, image_path)
        
        # Get CLIP model  
        clip_validator = get_clip_validator()
        if not clip_validator:
            return AttentionMapResponse(
                explanation="CLIP model unavailable - attention analysis not possible",
                error="Model unavailable"
            )
        
        # Generate attention map
        visualizer = get_attention_visualizer()
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: visualizer.generate_attention_map(
                image_path=image_path,
                text=text,
                clip_model=clip_validator
            )
        )

        if "error" in result:
            return AttentionMapResponse(
                explanation=f"Attention analysis failed: {result['error']}",
                error=result["error"]
            )
        
        logger.info(f"Attention heatmap generated for: '{text[:50]}...'")
        
        return AttentionMapResponse(**result)
        
    except Exception as e:
        logger.error(f"Attention heatmap failed: {e}")
        return AttentionMapResponse(
            explanation=f"Attention analysis failed: {str(e)}",
            error=str(e)
        )

@app.post("/api/xai/explain-enhanced")
async def get_enhanced_xai_explanation(
    image_result: Optional[Dict] = None,
    text_result: Optional[Dict] = None,
    voice_result: Optional[Dict] = None,
    include_discrepancies: bool = True,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Get comprehensive XAI explanation with multi-dimensional discrepancy detection.
    
    Phase 2: Enhanced XAI with brand, location, and condition checks.
    """
    try:
        from src.cross_modal.xai_explainer import XAIExplainer
        from src.cross_modal.enhanced_discrepancies import (
            check_brand_mismatch,
            check_location_consistency,
            check_condition_mismatch
        )
        
        explainer = XAIExplainer()
        
        # Get basic explanation
        base_explanation = explainer.generate_explanation(
            image_result=image_result,
            text_result=text_result,
            voice_result=voice_result
        )
        
        # Add enhanced discrepancy checks if requested
        if include_discrepancies:
            enhanced_checks = {}
            
            # Brand mismatch
            if image_result and text_result:
                brand_check = check_brand_mismatch(image_result, text_result)
                if brand_check.get("has_mismatch"):
                    enhanced_checks["brand_mismatch"] = brand_check
            
            # Location consistency (text vs voice)
            if text_result and voice_result:
                location_check = check_location_consistency(text_result, voice_result)
                if location_check.get("has_mismatch"):
                    enhanced_checks["location_inconsistency"] = location_check
            
            # Condition mismatch
            if image_result and text_result:
                condition_check = check_condition_mismatch(image_result, text_result)
                if condition_check.get("has_mismatch"):
                    enhanced_checks["condition_mismatch"] = condition_check
            
            if enhanced_checks:
                base_explanation["enhanced_checks"] = enhanced_checks
                base_explanation["has_discrepancy"] = True
                logger.info(f"Enhanced XAI: {len(enhanced_checks)} additional discrepancies detected")
        
        return base_explanation
        
    except Exception as e:
        logger.error(f"Enhanced XAI explanation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"XAI explanation failed: {str(e)}"
        )

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
                "overall_confidence": round(image_result["overall_score"] / 100.0, 3),
                "routing": "high_quality" if image_result["valid"] else "low_quality",
                "action": "forward_to_matching" if image_result["valid"] else "return_for_improvement",
                "individual_scores": {"image": round(image_result["overall_score"] / 100.0, 3)},
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
            metrics_collector.record_validation_result(
                "image",
                round(image_result["overall_score"] / 100.0, 3),
                "high_quality"
            )
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
    visualText: Optional[str] = Form(None),  # Visual-only text for CLIP (item+color+brand)
    image_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    language: str = Form("en"),
    # ---- Supabase routing fields (populated by authenticated frontend) ----
    intent: Optional[str] = Form(None),      # "lost" or "found"
    user_id: Optional[str] = Form(None),     # Firebase UID
    user_email: Optional[str] = Form(None),  # User email
    supabase_id: Optional[str] = Form(None), # Existing DB record ID to update
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
        # DEBUGGING: Log what text data we receive
        logger.info(f"[FRONTEND DATA] Received text parameter: '{text}'")
        logger.info(f"[FRONTEND DATA] Has image: {image_file is not None}, Has audio: {audio_file is not None}")
        
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
                # Use visualText for CLIP if available (visual attributes only), else use full text
                clip_text = visualText if visualText else text
                logger.info(f"[CLIP] Using text for validation: '{clip_text}' (visual_only={bool(visualText)})")
                clip_image_text_result = cached()(cv.validate_image_text_alignment)(image_path, clip_text)
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
        
        # Enhanced XAI Discrepancy Checks (Phase 2)
        logger.info(f"[XAI DEBUG] Checking discrepancies. Has image: {bool(image_result)}, Has text: {bool(text_result)}, Has voice: {bool(voice_result)}")
        if (image_result and text_result) or (text_result and voice_result):
            try:
                from src.cross_modal.enhanced_discrepancies import (
                    check_brand_mismatch, 
                    check_location_consistency, 
                    check_condition_mismatch,
                    check_color_mismatch
                )
                
                # Log what data we're passing
                logger.info(f"[XAI DEBUG] Text content: {text_result.get('text', 'N/A')[:100] if text_result else 'No text'}")
                logger.info(f"[XAI DEBUG] Image OCR: {image_result.get('ocr_text', 'N/A')[:100] if image_result else 'No image'}")
                logger.info(f"[XAI DEBUG] Text entities: {text_result.get('entities', {}) if text_result else {}}")
                
                brand_check = check_brand_mismatch(image_result, text_result, image_path) if image_result and text_result else {"has_mismatch": False}
                logger.info(f"[XAI DEBUG] Brand check: {brand_check}")
                
                # Pass cross_modal data to color check (contains CLIP mismatch detection)
                color_check = check_color_mismatch(image_result, text_result, cross_modal_results) if image_result and text_result else {"has_mismatch": False}
                logger.info(f"[XAI DEBUG] Color check: {color_check}")
                
                cond_check = check_condition_mismatch(image_result, text_result) if image_result and text_result else {"has_mismatch": False}
                logger.info(f"[XAI DEBUG] Condition check: {cond_check}")
                
                loc_check = check_location_consistency(text_result, voice_result) if text_result and voice_result else {"has_mismatch": False}
                logger.info(f"[XAI DEBUG] Location check: {loc_check}")
                
                has_discrepancy = (
                    brand_check.get("has_mismatch") or 
                    color_check.get("has_mismatch") or
                    loc_check.get("has_mismatch") or
                    cond_check.get("has_mismatch")
                )
                
                if has_discrepancy:
                    # Construct explanations for both UI Card and Legacy Chat
                    explanations = []
                    discrepancy_list = []
                    
                    if brand_check.get("has_mismatch"):
                        explanations.append(brand_check["explanation"])
                        discrepancy_list.append({"type": "Brand", "explanation": brand_check["explanation"]})
                    
                    if color_check.get("has_mismatch"):
                        explanations.append(color_check["explanation"])
                        discrepancy_list.append({"type": "Color", "explanation": color_check["explanation"]})
                        
                    if loc_check.get("has_mismatch"):
                        explanations.append(loc_check["explanation"])
                        discrepancy_list.append({"type": "Location", "explanation": loc_check["explanation"]})
                        
                    if cond_check.get("has_mismatch"):
                        explanations.append(cond_check["explanation"])
                        discrepancy_list.append({"type": "Condition", "explanation": cond_check["explanation"]})
                    
                    full_explanation = " ".join(explanations)
                    
                    cross_modal_results["xai_explanation"] = {
                        "has_discrepancy": True,
                        "explanation": full_explanation,
                        "severity": "medium", # Aggregate severity could be calculated
                        "details": {
                            "brand": brand_check,
                            "color": color_check,
                            "location": loc_check, 
                            "condition": cond_check
                        },
                        "discrepancies": discrepancy_list, # For legacy Chat support
                        "suggestion": "Please review the discrepancies highlighted above."
                    }
                    logger.info(f"Enhanced XAI Discrepancies found: {full_explanation}")
                    
            except Exception as e:
                logger.error(f"Enhanced XAI check failed: {e}")

        
        # ============================================================
        # Novel Feature #1: Spatial-Temporal Context Validation
        # ============================================================
        spatial_temporal_result = None
        if text_result:
            try:
                from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator
                
                # Extract context from text analysis
                completeness_entities = text_result.get("completeness", {}).get("entities", {}) or {}
                entities = text_result.get("entities", {}) or {}
                item_mentions = entities.get("item_mentions", [])
                location_mentions = entities.get("location_mentions", [])
                
                # Extract item type (prefer explicit entity extraction)
                item_type = None
                item_hints = completeness_entities.get("item_type", [])
                if item_hints and len(item_hints) > 0:
                    item_type = item_hints[0]
                elif item_mentions and len(item_mentions) > 0:
                    item_type = item_mentions[0]
                
                # Extract location (prefer explicit entity extraction)
                location = None
                location_hints = completeness_entities.get("location", [])
                if location_hints and len(location_hints) > 0:
                    location = location_hints[0]
                elif location_mentions and len(location_mentions) > 0:
                    location = location_mentions[0]
                
                # Extract time context
                time_val = None
                time_hints = completeness_entities.get("time", [])
                if time_hints and len(time_hints) > 0:
                    time_val = time_hints[0]
                
                if item_type and location:
                    st_validator = get_spatial_temporal_validator()
                    st_result = st_validator.calculate_plausibility(
                        item=item_type,
                        location=location,
                        time=time_val or "unknown"
                    )
                    spatial_temporal_result = st_result
                    logger.info(f"Spatial-Temporal: {item_type} @ {location} → {st_result.get('plausibility_score', 'N/A')}")
                    cross_modal_results["spatial_temporal"] = spatial_temporal_result
            except Exception as e:
                logger.warning(f"Spatial-temporal validation skipped: {e}")
        
        # Calculate overall confidence (must come AFTER cross_modal_results is fully populated)
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

        # ---- Sanitize numpy types for JSON serialization ----
        def sanitize_for_json(obj):
            """Recursively convert numpy types to native Python types."""
            import numpy as np
            if isinstance(obj, dict):
                return {k: sanitize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [sanitize_for_json(v) for v in obj]
            elif isinstance(obj, (np.bool_,)):
                return bool(obj)
            elif isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        # Final response structure
        response_data = sanitize_for_json({
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "input_types": input_types,
            "image": image_result,
            "text": text_result,
            "voice": voice_result,
            "cross_modal": cross_modal_results,
            "confidence": confidence_results,
            "feedback": feedback
        })
        
        # Update metrics
        if confidence_results["overall_confidence"] >= 0.7:
            metrics_collector.record_validation_result("multimodal", confidence_results["overall_confidence"], confidence_results["routing"])
        else:
            metrics_collector.record_validation_failure("multimodal", "low_confidence")
        
        # Phase 3: External Integration - Forward to Matching Engine
        if confidence_results.get("action") == "forward_to_matching":
            pass # Removed obsolete ExternalIntegrationService

        persist_validation_result(request_id, response_data)
        
        # ------------------------------------------------------------------ #
        # Supabase Persistence — save validated item into lost_items/found_items
        # Only runs when intent + user_id are provided AND confidence is sufficient
        # ------------------------------------------------------------------ #
        supabase_id = None
        if intent and user_id and confidence_results.get("overall_confidence", 0) >= 0.5:
            try:
                from src.database.supabase_client import get_supabase_manager
                sm = get_supabase_manager()
                if sm:
                    # Build item_data from validated results
                    item_data = {
                        "description": text or "",
                        "confidence_score": confidence_results.get("overall_confidence"),
                        "routing": confidence_results.get("routing", "manual"),
                        "action": confidence_results.get("action", "review"),
                        "validation_summary": {
                            "input_types": input_types,
                            "individual_scores": confidence_results.get("individual_scores", {}),
                            "cross_modal_scores": confidence_results.get("cross_modal_scores", {}),
                            "request_id": request_id,
                        },
                    }
                    # Pull structured fields from text validator entities if available
                    if text_result:
                        entities = text_result.get("entities", {}) or {}
                        completeness = text_result.get("completeness", {}).get("entities", {}) or {}
                        item_data["item_type"] = (completeness.get("item_type") or [None])[0] or ""
                        item_data["color"] = (completeness.get("color") or entities.get("color_mentions") or [None])[0] or ""
                        item_data["brand"] = (completeness.get("brand") or entities.get("brand_mentions") or [None])[0] or ""
                        item_data["location"] = (completeness.get("location") or entities.get("location_mentions") or [None])[0] or ""
                        item_data["time"] = (completeness.get("time") or [None])[0] or ""
                    
                    # Note: image_path is still valid here (cleanup scheduled later)
                    supabase_id_saved, sup_image_url = sm.save_validated_item(
                        intention=intent,
                        user_id=user_id,
                        user_email=user_email or "",
                        item_data=item_data,
                        image_path=image_path,  # SupabaseManager uploads then returns URL
                        supabase_id=supabase_id,
                    )
                    if supabase_id_saved:
                        response_data["supabase_id"] = supabase_id_saved
                        if sup_image_url:
                            response_data["image_url"] = sup_image_url
                        logger.info(f"✓ Saved to Supabase ({intent}_items): id={supabase_id}")
            except Exception as exc:
                logger.error(f"Supabase save failed (non-fatal): {exc}")
        
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
    Supports heartbeat mechanism to keep connection alive.
    """
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({"status": "connected", "client_id": client_id})
        
        # Wait for messages
        while True:
            try:
                # Receive with timeout to detect dead connections
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                
                # Handle heartbeat/ping messages
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    logger.debug(f"WebSocket ping/pong from {client_id}")
                    continue
                
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
                else:
                    logger.debug(f"WebSocket message from {client_id}: {data.get('type', 'unknown')}")
            
            except asyncio.TimeoutError:
                # No message received in 60 seconds, send ping to check if client is alive
                try:
                    await websocket.send_json({"type": "ping"})
                    logger.debug(f"Sent server-side ping to {client_id}")
                except Exception as e:
                    logger.warning(f"Failed to send ping to {client_id}: {e}")
                    break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {str(e)}", exc_info=True)
    finally:
        # Remove connection from active connections
        if client_id in active_connections:
            del active_connections[client_id]
            logger.info(f"WebSocket connection removed for {client_id}")

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

# ──────────────── Frontend Page Routes ────────────────
from fastapi.responses import HTMLResponse





# Serve static files (js, css, images)
# Serve static files (React build)
# Use absolute paths to avoid working directory issues
current_dir = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(current_dir, "frontend", "dist")
assets_dir = os.path.join(dist_dir, "assets")

logger.info(f"Serving static files from: {dist_dir}")
logger.info(f"Assets directory: {assets_dir}")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
else:
    logger.warning(f"Assets directory not found at {assets_dir}, UI may not load correctly.")

# SPA Fallback for React Router
# Explicit root handler to ensure SPA is served
@app.get("/")
async def serve_root():
    # Serve the index.html from dist
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return Response("Frontend not found", status_code=500)

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # API routes should be handled by their respective routers
    if full_path.startswith("api") or full_path.startswith("ws"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # Try to serve file if it exists (e.g. favicon.ico, logo.png)
    file_path = os.path.join(dist_dir, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
        
    # Otherwise return index.html for SPA routing
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return Response("Frontend not found", status_code=500)

# Main entry point
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
