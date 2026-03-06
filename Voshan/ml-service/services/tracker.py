"""
Multi-Object Tracking Service
Uses BoTSORT tracker for consistent object IDs across frames
"""

from ultralytics import YOLO
from typing import List, Dict, Tuple
import numpy as np


class ObjectTracker:
    """BoTSORT tracker wrapper for YOLO"""
    
    def __init__(self, model, tracker_config: str = "botsort.yaml"):
        """
        Initialize tracker
        
        Args:
            model: YOLO model instance
            tracker_config: Tracker configuration file
        """
        self.model = model
        self.tracker_config = tracker_config
        self.track_history = {}  # Track ID -> list of positions over time
    
    def track(self, frame: np.ndarray, persist: bool = True) -> List[Dict]:
        """
        Track objects in a frame
        
        Args:
            frame: Input frame as numpy array
            persist: Whether to persist tracks across frames
            
        Returns:
            List of tracked objects, each with:
            - track_id: int (persistent ID)
            - bbox: [x1, y1, x2, y2]
            - confidence: float
            - class_id: int
            - class_name: str
        """
        # Validate frame format
        if frame is None or frame.size == 0:
            return []
        
        # Ensure frame is in correct format
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            return []
        
        # Run tracking with error handling
        try:
            results = self.model.track(
                frame,
                persist=persist,
                tracker=self.tracker_config,
                verbose=False,
                imgsz=640
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "optical flow" in error_msg or "lkpyramid" in error_msg or "prevpyr" in error_msg or "lvlstep" in error_msg or "215" in error_msg or "assertion failed" in error_msg:
                try:
                    results = self.model.predict(
                        frame,
                        verbose=False,
                        imgsz=640
                    )
                    if len(results) > 0 and results[0].boxes is not None:
                        results[0].boxes.id = None
                except Exception:
                    return []
            else:
                raise
        
        tracked_objects = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            
            # Check if tracking IDs are available
            has_track_ids = boxes.id is not None
            
            for i in range(len(boxes)):
                box = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                cls_name = self.model.names[cls_id]
                
                # Get track ID if available
                track_id = int(boxes.id[i].cpu().numpy()) if has_track_ids else None
                
                # Update track history
                if track_id is not None:
                    if track_id not in self.track_history:
                        self.track_history[track_id] = []
                    
                    # Calculate center point
                    center_x = (box[0] + box[2]) / 2
                    center_y = (box[1] + box[3]) / 2
                    
                    self.track_history[track_id].append({
                        "center": (center_x, center_y),
                        "bbox": box.tolist(),
                        "class_id": cls_id,
                        "timestamp": len(self.track_history[track_id])  # Frame number
                    })
                    
                    # Keep only last 100 positions
                    if len(self.track_history[track_id]) > 100:
                        self.track_history[track_id] = self.track_history[track_id][-100:]
                
                tracked_objects.append({
                    "track_id": track_id,
                    "bbox": box.tolist(),
                    "confidence": conf,
                    "class_id": cls_id,
                    "class_name": cls_name
                })
        
        return tracked_objects
    
    def get_track_history(self, track_id: int) -> List[Dict]:
        """Get position history for a specific track ID"""
        return self.track_history.get(track_id, [])
    
    def calculate_speed(self, track_id: int, fps: float = 30.0) -> float:
        """
        Calculate speed of a tracked object in pixels/second
        
        Args:
            track_id: Track ID
            fps: Frames per second of video
            
        Returns:
            Speed in pixels/second
        """
        history = self.get_track_history(track_id)
        if len(history) < 2:
            return 0.0
        
        # Get last two positions
        pos1 = history[-2]["center"]
        pos2 = history[-1]["center"]
        
        # Calculate distance
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        distance = np.sqrt(dx**2 + dy**2)
        
        # Convert to pixels per second
        time_diff = 1.0 / fps  # Time between frames
        speed = distance / time_diff
        
        return speed
    
    def clear_history(self):
        """Clear all track history"""
        self.track_history = {}

