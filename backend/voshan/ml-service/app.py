"""
Flask Application for Suspicious Behavior Detection ML Service
"""

import os
import yaml
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import numpy as np
import cv2

from services.detector import YOLODetector
from services.tracker import ObjectTracker
from services.behavior import BehaviorDetector
from utils.video import VideoProcessor
from utils.alerts import AlertManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

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
    if detector is None or tracker is None or behavior_detector is None:
        return jsonify({
            "status": "error",
            "message": "Services not initialized"
        }), 500
    
    try:
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
        video_path = os.path.join(upload_dir, filename)
        video_file.save(video_path)
        
        # Get video info
        video_info = video_processor.get_video_info(video_path)
        behavior_detector.fps = video_info['fps']
        
        # Read video frames
        logger.info(f"Reading video: {video_path}")
        frames, _ = video_processor.read_video(video_path)
        logger.info(f"Read {len(frames)} frames")
        
        # Process frames
        all_detections = []
        all_alerts = []
        annotated_frames = []
        
        behavior_detector.reset()
        
        for i, frame in enumerate(frames):
            # Calculate current time from video
            current_time = i / video_info['fps']
            
            # Track objects
            tracked_objects = tracker.track(frame, persist=config['tracking']['persist'])
            
            # Detect behaviors
            frame_alerts = behavior_detector.process_frame(tracked_objects, current_time=current_time)
            
            # Store results
            all_detections.append(tracked_objects)
            all_alerts.extend(frame_alerts)
            
            # Annotate frame
            annotated_frame = video_processor.draw_detections(frame, tracked_objects)
            annotated_frame = video_processor.draw_alerts(annotated_frame, frame_alerts)
            annotated_frames.append(annotated_frame)
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(frames)} frames")
        
        logger.info(f"Processing complete. Generated {len(all_alerts)} alerts")
        
        # Save annotated video if requested
        output_video_path = None
        save_output = request.form.get('save_output', 'true').lower() == 'true'
        
        if save_output:
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
        formatted_alerts = [AlertManager.format_alert(alert) for alert in all_alerts]
        
        response = {
            "status": "success",
            "video_info": video_info,
            "total_frames": len(frames),
            "total_detections": sum(len(d) for d in all_detections),
            "total_alerts": len(formatted_alerts),
            "alerts": formatted_alerts,
            "log_json": alerts_json_path,
            "log_csv": alerts_csv_path
        }
        
        if output_video_path:
            response["output_video"] = output_video_path
        
        # Clean up uploaded file
        try:
            os.remove(video_path)
        except:
            pass
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
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

