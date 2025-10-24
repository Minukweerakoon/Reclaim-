import os
import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Union, Optional
from ultralytics import YOLO
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ImageValidator')

class ImageValidator:
    """A comprehensive image validation system for lost and found applications.
    
    This class provides methods to validate images based on various criteria:
    - File size and format validation
    - Blur detection using Laplacian variance
    - Object detection using YOLOv8
    - Face detection and privacy protection
    
    The validation pipeline returns structured results in JSON format.
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, 
                 blur_threshold: float = 100.0,
                 object_confidence: float = 0.85,
                 yolo_model_path: str = 'yolov8n.pt',
                 enable_logging: bool = True):
        """Initialize the ImageValidator with configurable parameters.
        
        Args:
            blur_threshold: Threshold for Laplacian variance blur detection (default: 100.0)
            object_confidence: Confidence threshold for object detection (default: 0.85)
            yolo_model_path: Path to the YOLOv8 model file (default: 'yolov8n.pt')
            enable_logging: Whether to enable logging (default: True)
        """
        self.blur_threshold = blur_threshold
        self.object_confidence = object_confidence
        self.enable_logging = enable_logging
        
        # Initialize YOLOv8 model
        try:
            self.yolo_model = YOLO(yolo_model_path)
            if self.enable_logging:
                logger.info(f"YOLOv8 model loaded from {yolo_model_path}")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Failed to load YOLOv8 model: {str(e)}")
            raise
    
    def validate_image(self, image_path: str) -> Dict:
        """Main validation pipeline that processes an image and returns structured results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict containing validation results with the following structure:
            {
                "valid": bool,  # Overall validity of the image
                "file_validation": {  # File validation results
                    "valid": bool,
                    "format": str,
                    "size": int,
                    "message": str
                },
                "blur_detection": {  # Blur detection results
                    "valid": bool,
                    "variance": float,
                    "threshold": float,
                    "message": str
                },
                "object_detection": {  # Object detection results
                    "valid": bool,
                    "objects": List[Dict],
                    "message": str
                },
                "privacy_protection": {  # Privacy protection results
                    "faces_detected": int,
                    "faces_blurred": int,
                    "message": str
                },
                "processing_time": float,  # Total processing time in seconds
                "message": str  # Overall validation message
            }
        """
        start_time = time.time()
        
        # Initialize result structure
        result = {
            "valid": False,
            "file_validation": {},
            "blur_detection": {},
            "object_detection": {},
            "privacy_protection": {},
            "processing_time": 0,
            "message": ""
        }
        
        try:
            # Step 1: Validate file format and size
            file_validation = self.validate_file(image_path)
            result["file_validation"] = file_validation
            
            if not file_validation["valid"]:
                result["message"] = "File validation failed: " + file_validation["message"]
                result["processing_time"] = time.time() - start_time
                return result
            
            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                result["message"] = "Failed to load image: The image file may be corrupted"
                result["processing_time"] = time.time() - start_time
                return result
            
            # Step 2: Perform blur detection
            blur_detection = self.detect_blur(image)
            result["blur_detection"] = blur_detection
            
            # Step 3: Perform object detection
            object_detection = self.detect_objects(image_path)
            result["object_detection"] = object_detection
            
            # Step 4: Perform face detection and privacy protection
            privacy_protection = self.protect_privacy(image)
            result["privacy_protection"] = privacy_protection
            
            # Determine overall validity
            result["valid"] = (
                file_validation["valid"] and 
                blur_detection["valid"] and 
                object_detection["valid"]
            )
            
            if result["valid"]:
                result["message"] = "Image passed all validation checks"
            else:
                failed_checks = []
                if not file_validation["valid"]:
                    failed_checks.append("file validation")
                if not blur_detection["valid"]:
                    failed_checks.append("blur detection")
                if not object_detection["valid"]:
                    failed_checks.append("object detection")
                
                result["message"] = f"Image failed validation: {', '.join(failed_checks)}"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during image validation: {str(e)}")
            result["message"] = f"Error during validation: {str(e)}"
        
        # Calculate total processing time
        result["processing_time"] = time.time() - start_time
        
        return result
    
    def validate_file(self, image_path: str) -> Dict:
        """Validate image file format and size.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict containing file validation results
        """
        result = {
            "valid": False,
            "format": "",
            "size": 0,
            "message": ""
        }
        
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                result["message"] = "File does not exist"
                return result
            
            # Get file extension
            _, ext = os.path.splitext(image_path.lower())
            result["format"] = ext
            
            # Check if format is supported
            if ext not in self.SUPPORTED_FORMATS:
                result["message"] = f"Unsupported image format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                return result
            
            # Check file size
            file_size = os.path.getsize(image_path)
            result["size"] = file_size
            
            if file_size > self.MAX_FILE_SIZE:
                result["message"] = f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
                return result
            
            # All checks passed
            result["valid"] = True
            result["message"] = "File validation passed"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during file validation: {str(e)}")
            result["message"] = f"Error during file validation: {str(e)}"
        
        return result
    
    def detect_blur(self, image: np.ndarray) -> Dict:
        """Detect if an image is blurry using Laplacian variance.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dict containing blur detection results
        """
        result = {
            "valid": False,
            "variance": 0.0,
            "threshold": self.blur_threshold,
            "message": ""
        }
        
        try:
            # Convert image to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            result["variance"] = variance
            
            # Determine if image is sharp enough
            if variance >= self.blur_threshold:
                result["valid"] = True
                result["message"] = f"Image is sharp (variance: {variance:.2f})"
            else:
                result["message"] = f"Image is too blurry (variance: {variance:.2f}, threshold: {self.blur_threshold})"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during blur detection: {str(e)}")
            result["message"] = f"Error during blur detection: {str(e)}"
        
        return result
    
    def detect_objects(self, image_path: str) -> Dict:
        """Detect objects in an image using YOLOv8.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict containing object detection results
        """
        result = {
            "valid": False,
            "objects": [],
            "message": ""
        }
        
        try:
            # Run YOLOv8 inference
            yolo_results = self.yolo_model(image_path, conf=self.object_confidence)
            
            # Process results
            detected_objects = []
            for r in yolo_results:
                boxes = r.boxes
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # Get confidence and class
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    name = r.names[cls]
                    
                    # Add to detected objects list
                    detected_objects.append({
                        "class": name,
                        "confidence": conf,
                        "bbox": [x1, y1, x2, y2]
                    })
            
            result["objects"] = detected_objects
            
            # Determine if any relevant objects were detected
            if len(detected_objects) > 0:
                result["valid"] = True
                result["message"] = f"Detected {len(detected_objects)} objects with confidence >= {self.object_confidence}"
            else:
                result["message"] = f"No objects detected with confidence >= {self.object_confidence}"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during object detection: {str(e)}")
            result["message"] = f"Error during object detection: {str(e)}"
        
        return result
    
    def protect_privacy(self, image: np.ndarray) -> Dict:
        """Detect faces and apply privacy protection (blurring).
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dict containing privacy protection results and the processed image
        """
        result = {
            "faces_detected": 0,
            "faces_blurred": 0,
            "message": ""
        }
        
        try:
            # Load pre-trained face detector
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            result["faces_detected"] = len(faces)
            
            # Create a copy of the image for blurring faces
            blurred_image = image.copy()
            
            # Apply blurring to each detected face
            for (x, y, w, h) in faces:
                # Extract the face region
                face_roi = blurred_image[y:y+h, x:x+w]
                
                # Apply a strong blur to the face region
                blurred_face = cv2.GaussianBlur(face_roi, (99, 99), 30)
                
                # Replace the face region with the blurred version
                blurred_image[y:y+h, x:x+w] = blurred_face
                
                result["faces_blurred"] += 1
            
            if result["faces_detected"] > 0:
                result["message"] = f"Detected and blurred {result['faces_blurred']} faces for privacy protection"
            else:
                result["message"] = "No faces detected in the image"
            
            # Store the blurred image in the result
            result["blurred_image"] = blurred_image
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during privacy protection: {str(e)}")
            result["message"] = f"Error during privacy protection: {str(e)}"
        
        return result
    
    def save_processed_image(self, image: np.ndarray, output_path: str) -> bool:
        """Save a processed image to disk.
        
        Args:
            image: OpenCV image array
            output_path: Path where the image should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cv2.imwrite(output_path, image)
            if self.enable_logging:
                logger.info(f"Processed image saved to {output_path}")
            return True
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error saving processed image: {str(e)}")
            return False