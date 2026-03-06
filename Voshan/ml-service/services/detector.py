"""
YOLO Detection Service
Handles model loading and inference
"""

import os
import torch
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import numpy as np


class YOLODetector:
    """Wrapper for YOLO model detection"""
    
    def __init__(self, model_path: str, image_size: int = 800, confidence: float = 0.25, device: str = "cuda:0"):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to .pt model file
            image_size: Input image size
            confidence: Detection confidence threshold
            device: Device to run on ("cuda:0" or "cpu")
        """
        self.model_path = model_path
        self.image_size = image_size
        self.confidence = confidence
        self.device = device if torch.cuda.is_available() and "cuda" in device else "cpu"
        
        # Load model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")
        
        print(f"Loading YOLO model from: {model_path}")
        self.model = YOLO(model_path)
        self.model.to(self.device)
        print(f"Model loaded successfully on device: {self.device}")
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Run detection on a single frame
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            List of detections, each with:
            - bbox: [x1, y1, x2, y2]
            - confidence: float
            - class_id: int (0=bag, 1=person)
            - class_name: str
        """
        results = self.model.predict(
            frame,
            imgsz=self.image_size,
            conf=self.confidence,
            device=self.device,
            verbose=False
        )
        
        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                # Get box coordinates
                box = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                cls_name = self.model.names[cls_id]
                
                detections.append({
                    "bbox": box.tolist(),  # [x1, y1, x2, y2]
                    "confidence": conf,
                    "class_id": cls_id,
                    "class_name": cls_name
                })
        
        return detections
    
    def detect_batch(self, frames: List[np.ndarray]) -> List[List[Dict]]:
        """
        Run detection on multiple frames (optimized batch processing)
        
        Args:
            frames: List of frames as numpy arrays
            
        Returns:
            List of detection lists (one per frame)
        """
        # Use YOLO's batch prediction for better performance
        if len(frames) == 0:
            return []
        
        # Run batch prediction (much faster than individual predictions)
        results = self.model.predict(
            frames,  # Pass list of frames directly
            imgsz=self.image_size,
            conf=self.confidence,
            device=self.device,
            verbose=False
        )
        
        all_detections = []
        for result in results:
            detections = []
            if result.boxes is not None:
                boxes = result.boxes
                for i in range(len(boxes)):
                    # Get box coordinates
                    box = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    cls_name = self.model.names[cls_id]
                    
                    detections.append({
                        "bbox": box.tolist(),  # [x1, y1, x2, y2]
                        "confidence": conf,
                        "class_id": cls_id,
                        "class_name": cls_name
                    })
            all_detections.append(detections)
        
        return all_detections
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            "model_path": self.model_path,
            "image_size": self.image_size,
            "confidence": self.confidence,
            "device": self.device,
            "classes": self.model.names if hasattr(self.model, 'names') else {}
        }

