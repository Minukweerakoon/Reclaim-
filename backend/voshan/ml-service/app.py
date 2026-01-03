"""
Flask Application for Suspicious Behavior Detection ML Service
"""

import os
import yaml
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import numpy as np
import cv2
import traceback

# Configure logging first (needed for import warnings)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import flask-compress for response compression (optional)
try:
    from flask_compress import Compress
    COMPRESS_AVAILABLE = True
except ImportError:
    COMPRESS_AVAILABLE = False
    logger.warning("flask-compress not available. Response compression disabled. Install with: pip install flask-compress")

from services.detector import YOLODetector
from services.tracker import ObjectTracker
from services.behavior import BehaviorDetector
from utils.video import VideoProcessor
from utils.alerts import AlertManager

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Enable response compression to reduce response size (if available)
if COMPRESS_AVAILABLE:
    Compress(app)
    logger.info("Response compression enabled")
else:
    # Use Flask's built-in compression if available (Flask 2.2+)
    try:
        app.config['COMPRESS_MIMETYPES'] = ['application/json', 'text/html']
        app.config['COMPRESS_LEVEL'] = 6
    except:
        pass

# Configure Flask to return JSON errors instead of HTML
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Global error handler to ensure all errors return JSON
@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors and return JSON instead of HTML"""
    error_trace = traceback.format_exc()
    logger.error(f"Internal server error: {str(error)}")
    logger.error(f"Traceback: {error_trace}")
    
    # Get the actual exception if available
    from werkzeug.exceptions import InternalServerError
    if isinstance(error, InternalServerError):
        original_error = error.original_exception if hasattr(error, 'original_exception') else error
        error_msg = str(original_error) if original_error else str(error)
    else:
        error_msg = str(error) if error else "Unknown error"
    
    response = jsonify({
        "status": "error",
        "message": "Internal server error",
        "error": error_msg,
        "traceback": error_trace if app.debug else None
    })
    response.status_code = 500
    response.headers['Content-Type'] = 'application/json'
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    error_trace = traceback.format_exc()
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(f"Exception type: {type(e).__name__}")
    logger.error(f"Traceback: {error_trace}")
    
    # Pass through HTTPException (like 404, 400) to Flask's default handler
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    
    return jsonify({
        "status": "error",
        "message": "An error occurred while processing the request",
        "error": str(e),
        "error_type": type(e).__name__,
        "traceback": error_trace if app.debug else None
    }), 500

# Before request handler to log requests
@app.before_request
def log_request_info():
    """Log request information for debugging"""
    if request.method == 'POST' and request.path == '/api/v1/detect/process-video':
        logger.info(f"Video upload request received")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Files in request: {list(request.files.keys())}")
        if 'video_file' in request.files:
            logger.info(f"Video file: {request.files['video_file'].filename}")

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Initialize services
detector = None
tracker = None
behavior_detector = None
video_processor = VideoProcessor()

def initialize_services():
    """Initialize ML services"""
    global detector, tracker, behavior_detector
    
    try:
        model_path = os.path.join(os.path.dirname(__file__), config['model']['path'])
        detector = YOLODetector(
            model_path=model_path,
            image_size=config['model']['image_size'],
            confidence=config['model']['confidence'],
            device=config['model']['device']
        )
        
        tracker = ObjectTracker(
            model=detector.model,
            tracker_config=config['tracking']['tracker']
        )
        
        behavior_detector = BehaviorDetector(
            owner_max_dist=config['behavior']['owner_max_dist'],
            owner_absent_sec=config['behavior']['owner_absent_sec'],
            loiter_near_radius=config['behavior']['loiter_near_radius'],
            loiter_near_sec=config['behavior']['loiter_near_sec'],
            running_speed=config['behavior']['running_speed'],
            fps=30.0  # Default, will be updated from video
        )
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

# Initialize on startup
try:
    initialize_services()
except Exception as e:
    logger.error(f"Initialization failed: {e}")
    # Services will be None, endpoints will return errors

@app.route('/api/v1/detect/status', methods=['GET'])
def status():
    """Health check endpoint"""
    if detector is None:
        return jsonify({
            "status": "error",
            "message": "Services not initialized"
        }), 500
    
    try:
        model_info = detector.get_model_info()
        return jsonify({
            "status": "healthy",
            "model_loaded": True,
            "model_info": model_info,
            "gpu_available": config['model']['device'].startswith('cuda')
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/detect/process-video', methods=['POST'])
def process_video():
    """
    Process a video file and detect suspicious behaviors
    
    Request:
        - video_file: Video file (multipart/form-data)
        - output_path: Optional output path for annotated video
        - save_output: Whether to save annotated video (default: true)
    
    Response:
        - detections: List of detections per frame
        - alerts: List of suspicious behavior alerts
        - output_video: Path to annotated video (if saved)
        - log_json: Path to alerts JSON file
    """
    global tracker  # Required because we may reassign tracker on error recovery
    
    if detector is None or tracker is None or behavior_detector is None:
        return jsonify({
            "status": "error",
            "message": "Services not initialized"
        }), 500
    
    try:
        logger.info("Received video processing request")
        # Check if video file is in request
        if 'video_file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No video file provided"
            }), 400
        
        video_file = request.files['video_file']
        if video_file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No video file selected"
            }), 400
        
        # Save uploaded file temporarily
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(video_file.filename)
        if not filename:
            # If secure_filename returns empty, use timestamp
            import time
            filename = f"video_{int(time.time())}.mp4"
        
        video_path = os.path.join(upload_dir, filename)
        
        try:
            logger.info(f"Saving video file: {filename} (Content-Type: {video_file.content_type})")
            video_file.save(video_path)
            
            # Verify file was saved
            if not os.path.exists(video_path):
                raise ValueError(f"Failed to save video file to {video_path}")
            
            file_size = os.path.getsize(video_path)
            logger.info(f"Video file saved successfully. Size: {file_size} bytes")
            
        except Exception as save_error:
            logger.error(f"Error saving video file: {save_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "status": "error",
                "message": "Failed to save uploaded video file",
                "error": str(save_error)
            }), 500
        
        # Get video info
        try:
            video_info = video_processor.get_video_info(video_path)
            logger.info(f"Video info: {video_info}")
            
            if video_info['fps'] <= 0:
                logger.warning(f"Invalid FPS: {video_info['fps']}, using default 30.0")
                video_info['fps'] = 30.0
            
            behavior_detector.fps = video_info['fps']
        except Exception as info_error:
            logger.error(f"Error getting video info: {info_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Clean up uploaded file
            try:
                os.remove(video_path)
            except:
                pass
            return jsonify({
                "status": "error",
                "message": "Failed to read video file information",
                "error": str(info_error),
                "suggestion": "The video file may be corrupted or in an unsupported format"
            }), 400
        
        # Get processing options
        save_output = request.form.get('save_output', 'true').lower() == 'true'
        
        # Process frames using streaming (don't load all into memory)
        # Note: Tracking requires sequential processing, so we process frames one-by-one
        # but optimize by only annotating when needed
        logger.info(f"Processing video: {video_path}")
        
        all_detections = []
        all_alerts = []
        annotated_frames = []
        
        behavior_detector.reset()
        
        # Open video for streaming
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Get frame dimensions to ensure consistency
        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            raise ValueError("Cannot read first frame from video")
        
        frame_height, frame_width = first_frame.shape[:2]
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
        
        # Track previous frame dimensions for consistency check
        prev_frame_shape = (frame_height, frame_width)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Ensure frame dimensions are consistent (fix for tracker optical flow)
            # This is critical for BoTSORT tracker which uses optical flow
            current_shape = frame.shape[:2]
            if current_shape != prev_frame_shape:
                logger.warning(f"Frame size changed from {prev_frame_shape} to {current_shape}, resizing to {frame_width}x{frame_height}")
                frame = cv2.resize(frame, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)
                # Reset tracker if frame size changed to avoid optical flow errors
                # Note: This will lose track continuity, but prevents crashes
                if frame_count > 0:
                    logger.warning("Frame size changed during tracking - tracker state may be reset")
            
            # Ensure frame is in correct format (BGR, uint8)
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                logger.warning(f"Unexpected frame format: {frame.shape}, skipping frame")
                frame_count += 1
                continue
            
            # Calculate current time from video
            current_time = frame_count / video_info['fps']
            
            # Track objects (must be sequential for tracking to work correctly)
            # Wrap in try-except to handle optical flow errors gracefully
            try:
                tracked_objects = tracker.track(frame, persist=config['tracking']['persist'])
            except Exception as track_error:
                # If tracking fails due to optical flow error, reset and continue
                error_msg = str(track_error)
                if "optical flow" in error_msg.lower() or "lkpyramid" in error_msg.lower() or "prevPyr" in error_msg:
                    logger.error(f"Optical flow error at frame {frame_count}: {error_msg}")
                    logger.warning("Resetting tracker to recover from optical flow error")
                    # Create new tracker instance to reset internal state
                    tracker = ObjectTracker(
                        model=detector.model,
                        tracker_config=config['tracking']['tracker']
                    )
                    # Retry tracking with fresh tracker
                    try:
                        tracked_objects = tracker.track(frame, persist=config['tracking']['persist'])
                    except Exception as retry_error:
                        logger.error(f"Tracking failed after reset: {retry_error}")
                        tracked_objects = []  # Continue with empty detections
                else:
                    # Re-raise if it's a different error
                    raise
            
            # Detect behaviors
            frame_alerts = behavior_detector.process_frame(tracked_objects, current_time=current_time)
            
            # Store results
            all_detections.append(tracked_objects)
            all_alerts.extend(frame_alerts)
            
            # Annotate frame only if saving output
            if save_output:
                annotated_frame = video_processor.draw_detections(frame, tracked_objects)
                annotated_frame = video_processor.draw_alerts(annotated_frame, frame_alerts)
                annotated_frames.append(annotated_frame)
            
            # Update previous frame shape for next iteration
            prev_frame_shape = frame.shape[:2]
            
            frame_count += 1
            
            if frame_count % 100 == 0:
                logger.info(f"Processed {frame_count}/{total_frames} frames ({len(all_alerts)} alerts so far)")
        
        cap.release()
        logger.info(f"Processing complete. Generated {len(all_alerts)} alerts from {frame_count} frames")
        logger.info(f"Preparing response with {len(all_alerts)} alerts...")
        
        # Save annotated video if requested
        output_video_path = None
        
        if save_output and annotated_frames:
            output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
            os.makedirs(output_dir, exist_ok=True)
            output_filename = f"annotated_{filename}"
            output_video_path = os.path.join(output_dir, output_filename)
            video_processor.write_video(annotated_frames, output_video_path, fps=video_info['fps'])
            logger.info(f"Saved annotated video: {output_video_path}")
        
        # Save alerts
        alerts_dir = os.path.join(os.path.dirname(__file__), 'outputs')
        os.makedirs(alerts_dir, exist_ok=True)
        alerts_json_path = os.path.join(alerts_dir, f"alerts_{filename}.json")
        alerts_csv_path = os.path.join(alerts_dir, f"alerts_{filename}.csv")
        
        AlertManager.save_alerts_to_json(all_alerts, alerts_json_path)
        AlertManager.save_alerts_to_csv(all_alerts, alerts_csv_path)
        
        # Format response
        # Limit alerts in response to prevent connection resets (max 2000 alerts)
        # Full alerts are saved to JSON/CSV files which can be downloaded separately
        MAX_ALERTS_IN_RESPONSE = 2000
        try:
            formatted_alerts = [AlertManager.format_alert(alert) for alert in all_alerts]
            
            # Limit alerts in response to prevent large response sizes
            # Sort by severity (HIGH > MEDIUM > LOW > INFO) and timestamp (most recent first)
            if len(formatted_alerts) > MAX_ALERTS_IN_RESPONSE:
                severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0, "UNKNOWN": 0}
                formatted_alerts.sort(
                    key=lambda x: (
                        severity_order.get(x.get("severity", "UNKNOWN"), 0),
                        x.get("timestamp", 0)
                    ),
                    reverse=True
                )
                alerts_in_response = formatted_alerts[:MAX_ALERTS_IN_RESPONSE]
                logger.warning(
                    f"Response contains {len(alerts_in_response)} of {len(formatted_alerts)} total alerts. "
                    f"Full alerts available in log files."
                )
            else:
                alerts_in_response = formatted_alerts
                
        except Exception as format_error:
            logger.error(f"Error formatting alerts: {format_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            alerts_in_response = []
            formatted_alerts = []
        
        response = {
            "status": "success",
            "video_info": video_info,
            "total_frames": frame_count,
            "total_detections": sum(len(d) for d in all_detections),
            "total_alerts": len(formatted_alerts),
            "alerts_returned": len(alerts_in_response),
            "alerts": alerts_in_response,
            "log_json": alerts_json_path,
            "log_csv": alerts_csv_path,
            "note": f"Full alerts ({len(formatted_alerts)} total) saved to log files" if len(formatted_alerts) > len(alerts_in_response) else None
        }
        
        if output_video_path:
            response["output_video"] = output_video_path
        
        # Clean up uploaded file
        try:
            os.remove(video_path)
        except:
            pass
        
        # Return response
        try:
            return jsonify(response)
        except Exception as jsonify_error:
            logger.error(f"Error serializing response: {jsonify_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return minimal response as fallback
            return jsonify({
                "status": "success",
                "total_frames": frame_count,
                "total_alerts": len(formatted_alerts),
                "log_json": alerts_json_path,
                "log_csv": alerts_csv_path,
                "warning": "Response optimized due to serialization error"
            })
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error processing video: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        
        # Provide more helpful error messages for common issues
        if "optical flow" in error_msg.lower() or "lkpyramid" in error_msg.lower() or "prevPyr" in error_msg:
            return jsonify({
                "status": "error",
                "message": "Video frame size inconsistency detected. This video may have variable frame dimensions which causes tracking errors.",
                "error": error_msg,
                "suggestion": "The system will attempt to resize frames automatically. If the error persists, try using a video with consistent frame dimensions."
            }), 500
        
        # Clean up uploaded file on error
        try:
            if 'video_path' in locals() and os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up video file: {video_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up video file: {cleanup_error}")
        
        # Return detailed error
        return jsonify({
            "status": "error",
            "message": "Error processing video",
            "error": error_msg,
            "details": {
                "error_type": type(e).__name__,
                "traceback": error_trace if app.debug else None
            }
        }), 500

@app.route('/api/v1/detect/process-frame', methods=['POST'])
def process_frame():
    """
    Process a single frame (for real-time streaming)
    
    Request:
        - frame: Base64 encoded image or image file
        - camera_id: Optional camera identifier
    
    Response:
        - detections: List of detections
        - alerts: List of alerts for this frame
    """
    if detector is None or tracker is None or behavior_detector is None:
        return jsonify({
            "status": "error",
            "message": "Services not initialized"
        }), 500
    
    try:
        # Get frame data
        if 'frame' in request.files:
            # Image file
            frame_file = request.files['frame']
            frame_bytes = frame_file.read()
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        elif 'frame' in request.json:
            # Base64 encoded (would need to decode)
            return jsonify({
                "status": "error",
                "message": "Base64 encoding not yet implemented"
            }), 400
        else:
            return jsonify({
                "status": "error",
                "message": "No frame data provided"
            }), 400
        
        camera_id = request.form.get('camera_id') or request.json.get('camera_id')
        
        # Track objects
        tracked_objects = tracker.track(frame, persist=config['tracking']['persist'])
        
        # Detect behaviors
        frame_alerts = behavior_detector.process_frame(tracked_objects)
        
        # Format response
        formatted_alerts = [AlertManager.format_alert(alert, camera_id=camera_id) for alert in frame_alerts]
        
        return jsonify({
            "status": "success",
            "detections": tracked_objects,
            "alerts": formatted_alerts,
            "camera_id": camera_id
        })
    
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    host = config['api']['host']
    port = config['api']['port']
    debug = config['api']['debug']
    
    logger.info(f"Starting ML Service on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

