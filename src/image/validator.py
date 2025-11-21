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
        
        # Initialize face cascade for privacy protection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        if self.face_cascade.empty():
            if self.enable_logging:
                logger.error("Failed to load face cascade classifier.")
            raise IOError("Failed to load face cascade classifier.")
    
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
            "image_path": image_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sharpness": {},
            "objects": {},
            "privacy": {},
            "overall_score": 0.0,
            "valid": False
        }
        
        try:
            # Step 1: Validate file format and size
            file_validation = self.validate_file(image_path)
            if not file_validation["valid"]:
                result["sharpness"] = {"valid": False, "score": 0.0, "threshold": self.blur_threshold, "feedback": file_validation["message"]}
                result["objects"] = {"valid": False, "detections": [], "feedback": file_validation["message"]}
                result["privacy"] = {"faces_detected": 0, "privacy_protected": False, "processed_image": None, "feedback": file_validation["message"]}
                return result
            
            # Step 2: Perform sharpness detection
            sharpness_result = self.check_sharpness(image_path)
            result["sharpness"] = sharpness_result
            
            # Step 3: Perform object detection
            object_result = self.detect_objects(image_path)
            result["objects"] = object_result
            
            # Step 4: Perform face detection and privacy protection
            privacy_result = self.detect_privacy_content(image_path)
            result["privacy"] = privacy_result
            
            # Calculate overall score
            sharpness_score = sharpness_result["score"] / self.blur_threshold if sharpness_result["valid"] else 0.0
            object_score = 1.0 if object_result["valid"] else (0.4 if object_result["detections"] else 0.0)
            
            # Cap sharpness score at 1.0 if it exceeds threshold significantly
            if sharpness_score > 1.0: sharpness_score = 1.0

            overall_score = (0.6 * sharpness_score) + (0.4 * object_score)
            result["overall_score"] = round(overall_score, 2)
            
            # Determine overall validity
            result["valid"] = overall_score >= 0.70
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during image validation: {str(e)}")
            # Ensure all sub-results are marked as invalid on error
            result["sharpness"] = {"valid": False, "score": 0.0, "threshold": self.blur_threshold, "feedback": f"Error: {str(e)}"}
            result["objects"] = {"valid": False, "detections": [], "feedback": f"Error: {str(e)}"}
            result["privacy"] = {"faces_detected": 0, "privacy_protected": False, "processed_image": None, "feedback": f"Error: {str(e)}"}
            result["valid"] = False
        
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
    
    def check_sharpness(self, image_path: str) -> Dict:
        """Detect if an image is blurry using Laplacian variance.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dict containing blur detection results
        """
        result = {
            "valid": False,
            "score": 0.0,
            "threshold": self.blur_threshold,
            "feedback": ""
        }
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                result["feedback"] = "Failed to load image for sharpness check: The image file may be corrupted"
                return result

            # Convert image to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            result["score"] = variance
            
            # Determine if image is sharp enough
            if variance >= self.blur_threshold:
                result["valid"] = True
                result["feedback"] = f"Image is sharp (score: {variance:.2f})"
            else:
                result["feedback"] = f"Image is too blurry (score: {variance:.2f}, threshold: {self.blur_threshold})"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during blur detection: {str(e)}")
            result["feedback"] = f"Error during blur detection: {str(e)}"
        
        return result
    
    def detect_objects(self, image_path: str) -> Dict:
        """Detect objects in an image using YOLOv8."""

        result = {
            "valid": False,
            "detections": [],
            "feedback": ""
        }

        try:
            inference_conf = min(max(self.object_confidence, 0.05), 0.95)
            yolo_results = self.yolo_model(image_path, conf=inference_conf)

            detected_objects = []
            for r in yolo_results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    name = r.names[cls]
                    detected_objects.append({
                        "class": name,
                        "confidence": conf,
                        "bbox": [x1, y1, x2, y2]
                    })

            result["detections"] = [
                obj for obj in detected_objects if obj["confidence"] >= self.object_confidence
            ]

            if result["detections"]:
                result["valid"] = True
                result["feedback"] = (
                    f"Detected {len(result['detections'])} objects with confidence >= {self.object_confidence:.2f}"
                )
            else:
                if detected_objects:
                    top_detection = max(detected_objects, key=lambda o: o["confidence"])
                    result["detections"].append(top_detection)
                    result["feedback"] = (
                        f"No objects met the confidence threshold {self.object_confidence:.2f}. "
                        f"Top candidate: {top_detection['class']} @ {top_detection['confidence']:.2f}"
                    )
                else:
                    result["feedback"] = f"No objects detected (threshold {self.object_confidence:.2f})"

        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during object detection: {str(e)}")
            result["feedback"] = f"Error during object detection: {str(e)}"

        return result

    def detect_privacy_content(self, image_path: str) -> Dict:
        """Detect faces and apply privacy protection (blurring).
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dict containing privacy protection results and the processed image
        """
        result = {
            "faces_detected": 0,
            "privacy_protected": False,
            "processed_image": None,
            "feedback": ""
        }
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                result["feedback"] = "Failed to load image for privacy protection: The image file may be corrupted"
                return result

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            result["faces_detected"] = len(faces)
            
            # Create a copy of the image for blurring faces
            blurred_image = image.copy()
            
            # Apply blurring to each detected face
            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    # Extract the face region
                    face_roi = blurred_image[y:y+h, x:x+w]
                    
                    # Apply a strong blur to the face region
                    blurred_face = cv2.GaussianBlur(face_roi, (99, 99), 30)
                    
                    # Replace the face region with the blurred version
                    blurred_image[y:y+h, x:x+w] = blurred_face
                    
                # Save the blurred image to a temporary file
                output_dir = os.path.join(os.path.dirname(image_path), "processed")
                os.makedirs(output_dir, exist_ok=True)
                processed_image_path = os.path.join(output_dir, f"blurred_{os.path.basename(image_path)}")
                self.save_processed_image(blurred_image, processed_image_path)
                result["processed_image"] = processed_image_path
                result["privacy_protected"] = True
                result["feedback"] = f"Detected and blurred {len(faces)} faces for privacy protection. Processed image saved to {processed_image_path}"
            else:
                result["feedback"] = "No faces detected in the image"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during privacy protection: {str(e)}")
            result["feedback"] = f"Error during privacy protection: {str(e)}"
        
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




