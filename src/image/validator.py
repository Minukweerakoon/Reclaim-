import os
import time
import logging
from typing import Dict, List, Optional

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from PIL import Image as PILImage
import imagehash

from src.image.vit_validator import get_vit_validator, CATEGORY_ALIASES

# CLIP validator for fallback (lazy loaded)
_clip_validator = None

def get_clip_validator_for_fallback():
    """Lazy load CLIP validator for fallback validation."""
    global _clip_validator
    if _clip_validator is None:
        try:
            from src.cross_modal.clip_validator import CLIPValidator
            _clip_validator = CLIPValidator(enable_logging=False)
            logger.info("✓ CLIP validator loaded for fallback")
        except Exception as e:
            logger.warning(f"CLIP fallback unavailable: {e}")
            _clip_validator = False
    return _clip_validator if _clip_validator else None

logger = logging.getLogger("ImageValidator")
logger.setLevel(logging.INFO)


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization.
    Fixes PydanticSerializationError with numpy.bool_, numpy.int64, etc.
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


class ImageValidator:
    """
    Production-ready image validator that follows the research specification:
    - YOLOv8 object detection
    - Normalized sharpness scoring
    - 60/40 weighted final score with actionable feedback
    """

    SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".webp")
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(
        self,
        model_path: Optional[str] = None,
        enable_logging: bool = True,
        use_vit: bool = True,  # NEW: Use ViT by default
    ) -> None:
        self.enable_logging = enable_logging
        self.use_vit = use_vit
        
        # YOLOv11 model path resolution (latest YOLO version - 2024)
        if model_path:
            self.yolo_model_path = model_path
        else:
            # Use YOLOv11n (nano) - faster and more accurate than YOLOv8
            self.yolo_model_path = self._resolve_model_path("models/yolo11n.pt")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load YOLOv11 model (automatically downloads if not present)
        try:
            self.yolo_model = YOLO(self.yolo_model_path)
            logger.info(f"✓ Loaded YOLOv11 model on {self.device}")
        except Exception as e:
            logger.warning(f"YOLOv11 not found, falling back to YOLOv8: {e}")
            self.yolo_model_path = self._resolve_model_path("models/yolov8n.pt")
            self.yolo_model = YOLO(self.yolo_model_path)
        
        # Load ViT validator (95% accuracy model)
        if use_vit:
            try:
                self.vit_validator = get_vit_validator()
                if self.enable_logging:
                    logger.info("✓ ViT validator loaded (95% accuracy)")
            except Exception as e:
                logger.warning(f"Failed to load ViT: {e}. Falling back to YOLOv8.")
                self.vit_validator = None
                self.use_vit = False
        else:
            self.vit_validator = None
        
        if self.enable_logging:
            model_info = "ViT (95% accuracy)" if self.use_vit else f"YOLOv8 ({self.yolo_model_path})"
            logger.info(f"ImageValidator initialized with {model_info} on {self.device}")

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.profile_face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_profileface.xml"
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def validate_image(self, image_path: str, text: Optional[str] = None) -> Dict:
        start = time.time()

        file_check = self.validate_file(image_path)
        if not file_check["valid"]:
            return {
                "valid": False,
                "overall_score": 0.0,
                "sharpness": {
                    "valid": False,
                    "score": 0,
                    "feedback": file_check["message"],
                },
                "objects": {
                    "valid": False,
                    "detections": [],
                    "detection_score": 0,
                    "feedback": file_check["message"],
                },
                "privacy": {"faces_detected": 0, "privacy_protected": False, "processed_image": None, "feedback": file_check["message"]},
                "feedback": file_check["message"],
                "processing_time": round(time.time() - start, 3),
            }

        sharpness_result = self.check_sharpness(image_path)
        objects_result = self.detect_objects(image_path, text_hint=text)
        privacy_result = self.detect_privacy_content(image_path)

        sharpness_score = sharpness_result["score"] / 100
        detection_score = objects_result["detection_score"] / 100
        overall = (sharpness_score * 0.6 + detection_score * 0.4) * 100
        is_valid = overall >= 70

        # Research metadata (expose which model was used)
        model_used = objects_result.get("model", "YOLOv8")
        model_confidence = objects_result.get("confidence", detection_score)

        return {
            "valid": is_valid,
            "overall_score": round(overall, 1),
            "sharpness": sharpness_result,
            "objects": objects_result,
            "privacy": privacy_result,
            "feedback": self._generate_feedback(sharpness_result, objects_result, overall),
            "processing_time": round(time.time() - start, 3),
            # Research features metadata
            "research_metadata": {
                "model_used": model_used,
                "model_confidence": round(model_confidence, 3),
                "features_active": {
                    "custom_vit": model_used == "ViT-Custom-95%",
                    "detection_method": "deep_learning" 
                }
            }
        }

    def validate_file(self, image_path: str) -> Dict:
        result = {"valid": False, "message": "", "format": "", "size": 0}
        if not os.path.exists(image_path):
            result["message"] = "File does not exist"
            return result

        _, ext = os.path.splitext(image_path.lower())
        result["format"] = ext
        if ext not in self.SUPPORTED_FORMATS:
            result["message"] = f"Unsupported format: {ext}"
            return result

        size = os.path.getsize(image_path)
        result["size"] = size
        if size > self.MAX_FILE_SIZE:
            result["message"] = "File exceeds 10MB limit"
            return result

        result["valid"] = True
        result["message"] = "File validation passed"
        return result

    def check_sharpness(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            return {
                "valid": False,
                "score": 0.0,
                "raw_variance": 0.0,
                "feedback": "Cannot read image",
            }

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = float(laplacian.var())

        if variance < 50:
            normalized = (variance / 50.0) * 50.0
        elif variance < 200:
            normalized = 50.0 + ((variance - 50.0) / 150.0) * 30.0
        else:
            normalized = 80.0 + min(((variance - 200.0) / 300.0) * 20.0, 20.0)

        is_sharp = normalized >= 70
        return {
            "valid": is_sharp,
            "score": round(normalized, 1),
            "raw_variance": variance,
            "feedback": f"Image sharpness: {normalized:.0f}% - {'Good' if is_sharp else 'Needs improvement'}",
        }


    def detect_objects(self, image_path: str, text_hint: Optional[str] = None) -> Dict:
        """
        Detect objects using YOLO as primary detector (more reliable).
        ViT is used only as fallback when YOLO detects nothing.
        
        Args:
            image_path: Path to image
            text_hint: Optional text description (logged but not used for routing now)
        """
        # STRATEGY CHANGE: YOLO PRIMARY for ALL items
        # Reason: ViT misdetects phones→headphone, wallets→backpack
        # YOLO (80 COCO classes) is more reliable for general objects
        
        logger.info(f"[DETECTION] Text hint received: '{text_hint}'")
        logger.info(f"[DETECTION] Using YOLO-PRIMARY strategy for all items")
        
        # Try YOLOv11 FIRST (primary detector)
        try:
            results = self.yolo_model(image_path, conf=0.25, device=self.device, verbose=False)
            detections = []
            
            for result in results:
                if not result.boxes:
                    continue
                for box in result.boxes:
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = result.names.get(cls_id, "object")
                    
                    # Map YOLO classes to lost-and-found categories
                    mapped_class = self._map_yolo_class(class_name)
                    
                    detections.append({
                        "class": mapped_class,
                        "original_class": class_name,
                        "confidence": round(conf, 3),
                        "bbox": [float(x) for x in box.xyxy[0].tolist()],
                    })
            
            detections.sort(key=lambda x: x["confidence"], reverse=True)
            high_conf = [d for d in detections if d["confidence"] > 0.4]
            
            # If YOLO found something with decent confidence, use it
            if high_conf:
                detection_score = min(100, len(high_conf) * 50)
                logger.info(f"[DETECTION] YOLOv11 detected: {high_conf[0]['class']} ({high_conf[0]['confidence']})")
                return {
                    "valid": bool(True),
                    "confidence": float(high_conf[0]["confidence"]),
                    "detections": high_conf,
                    "detection_score": float(detection_score),
                    "feedback": self._generate_yolo_feedback(high_conf, detections),
                    "model": "YOLOv11-Primary"
                }
                
        except Exception as e:
            logger.error(f"YOLOv11 primary detection failed: {e}")
        
        # FALLBACK: Use ViT only if YOLO found nothing
        if self.use_vit and self.vit_validator:
            try:
                logger.info("[DETECTION] YOLO found nothing, falling back to ViT")
                vit_result = self.vit_validator.validate_image(image_path)
                
                vit_confidence = float(vit_result['confidence'])
                vit_item = str(vit_result['detected_item'])
                
                # ════════════════════════════════════════════════════════════
                # CLIP FALLBACK: If ViT is uncertain (<70%) and text provided,
                # use CLIP to validate text against image. Trust text if CLIP agrees.
                # ════════════════════════════════════════════════════════════
                final_item = vit_item
                final_confidence = vit_confidence
                used_clip_fallback = False
                clip_similarity = None
                
                if vit_confidence < 0.70 and text_hint:
                    logger.info(f"[CLIP FALLBACK] ViT uncertain ({vit_confidence:.1%}), validating with CLIP...")
                    clip_validator = get_clip_validator_for_fallback()
                    
                    if clip_validator:
                        try:
                            # Validate text description against image
                            clip_result = clip_validator.validate_image_text_alignment(image_path, text_hint)
                            clip_similarity = clip_result.get('similarity', 0)
                            
                            logger.info(f"[CLIP FALLBACK] Text-image similarity: {clip_similarity:.1%}")
                            
                            # If CLIP agrees with text description (>50% similarity), trust the text
                            if clip_similarity >= 0.50:
                                # Extract item from text hint using aliases
                                text_lower = text_hint.lower()
                                detected_from_text = None
                                
                                # Check aliases first
                                for category, aliases in CATEGORY_ALIASES.items():
                                    if any(alias in text_lower for alias in aliases):
                                        detected_from_text = category
                                        break
                                    if category in text_lower:
                                        detected_from_text = category
                                        break
                                
                                # Common item keywords
                                common_items = ['headphones', 'headset', 'phone', 'wallet', 'laptop', 
                                               'backpack', 'bag', 'keys', 'watch', 'glasses', 'card']
                                if not detected_from_text:
                                    for item in common_items:
                                        if item in text_lower:
                                            detected_from_text = item
                                            break
                                
                                if detected_from_text:
                                    logger.info(f"[CLIP FALLBACK] ✓ Trusting text description: '{detected_from_text}' (CLIP: {clip_similarity:.1%})")
                                    final_item = detected_from_text
                                    final_confidence = clip_similarity  # Use CLIP similarity as confidence
                                    used_clip_fallback = True
                                else:
                                    logger.info(f"[CLIP FALLBACK] Could not extract item from text, keeping ViT result")
                            else:
                                logger.info(f"[CLIP FALLBACK] CLIP similarity too low ({clip_similarity:.1%}), keeping ViT result")
                                
                        except Exception as clip_error:
                            logger.warning(f"[CLIP FALLBACK] CLIP validation failed: {clip_error}")
                
                # Format detections
                detailed_detections = []
                if used_clip_fallback:
                    # Primary detection from CLIP-validated text
                    detailed_detections.append({
                        "class": final_item,
                        "confidence": float(final_confidence),
                        "source": "text_description"
                    })
                    # Add ViT predictions as secondary
                    if 'all_predictions' in vit_result:
                        for item, conf in vit_result['all_predictions']:
                            detailed_detections.append({
                                "class": str(item),
                                "confidence": float(conf),
                                "source": "vit_secondary"
                            })
                else:
                    if 'all_predictions' in vit_result:
                        for item, conf in vit_result['all_predictions']:
                            detailed_detections.append({
                                "class": str(item),
                                "confidence": float(conf)
                            })
                    else:
                        detailed_detections.append({
                            "class": vit_item,
                            "confidence": vit_confidence
                        })

                # Generate feedback
                if used_clip_fallback:
                    feedback = f"✓ Detected {final_item} (validated against your description, {final_confidence:.0%} match)"
                elif vit_confidence >= 0.70:
                    feedback = f"✓ Detected {final_item} ({vit_confidence:.0%} confidence)"
                else:
                    feedback = f"⚠️ Uncertain: {final_item} ({vit_confidence:.0%}). "
                    if 'all_predictions' in vit_result and len(vit_result['all_predictions']) > 1:
                        alternatives = [f"{item} ({conf:.0%})" for item, conf in vit_result['all_predictions'][1:3]]
                        feedback += f"Could also be: {', '.join(alternatives)}"

                return {
                    "valid": bool(final_confidence >= 0.50 or used_clip_fallback),
                    "confidence": float(final_confidence),
                    "detections": detailed_detections,
                    "detection_score": float(min(100, final_confidence * 100)),
                    "feedback": feedback,
                    "model": "CLIP-Validated" if used_clip_fallback else vit_result.get('model', "ViT-Fallback"),
                    "model_loaded": vit_result.get('model_loaded', False),
                    "clip_fallback_used": used_clip_fallback,
                    "clip_similarity": clip_similarity,
                    "all_predictions": vit_result.get('all_predictions', [])
                }
            except Exception as e:
                logger.warning(f"ViT fallback also failed: {e}")
        
        # Last resort: Return no detection
        logger.warning("[DETECTION] Both YOLO and ViT failed to detect anything")
        return {
            "valid": bool(False),
            "confidence": float(0.0),
            "detections": [],
            "detection_score": float(0),
            "feedback": "No objects detected with sufficient confidence",
            "model": "None"
        }


    def detect_privacy_content(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            return {
                "faces_detected": 0,
                "privacy_protected": False,
                "processed_image": None,
                "feedback": "Cannot read image",
            }

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect frontal faces
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        faces_list = [list(f) for f in faces]
        
        # Detect profile faces
        profile_faces = self.profile_face_cascade.detectMultiScale(gray, 1.1, 4)
        for f in profile_faces:
            # Avoid duplicates (simple overlap check)
            is_duplicate = False
            fx, fy, fw, fh = f
            for (x, y, w, h) in faces_list:
                if abs(fx - x) < 20 and abs(fy - y) < 20:
                    is_duplicate = True
                    break
            if not is_duplicate:
                faces_list.append(list(f))
        
        if len(faces_list) == 0:
            return {
                "faces_detected": 0,
                "privacy_protected": False,
                "processed_image": None,
                "feedback": "No faces detected",
            }

        blurred = image.copy()
        blurred = image.copy()
        for (x, y, w, h) in faces_list:
            roi = blurred[y : y + h, x : x + w]
            # Aggressive blurring for privacy
            roi = cv2.GaussianBlur(roi, (99, 99), 30)
            blurred[y : y + h, x : x + w] = roi

        processed_dir = os.path.join(os.path.dirname(image_path), "processed")
        os.makedirs(processed_dir, exist_ok=True)
        processed_path = os.path.join(processed_dir, f"privacy_{os.path.basename(image_path)}")
        cv2.imwrite(processed_path, blurred)

        return {
            "faces_detected": len(faces_list),
            "privacy_protected": True,
            "processed_image": processed_path,
            "feedback": f"Blurred {len(faces_list)} face(s)",
        }

    def _generate_feedback(self, sharpness: Dict, objects: Dict, overall: float) -> str:
        if overall >= 85:
            return "Excellent image quality! Clear and recognizable."
        if overall >= 70:
            return "Good image quality. Item is visible."
        issues = []
        if sharpness.get("score", 0) < 70:
            issues.append("the image is blurry")
        if not objects.get("valid"):
            issues.append("the item is not clearly visible")
        issue_text = " and ".join(issues) if issues else "additional clarity is required"
        return f"Image quality needs improvement: {issue_text}. Try better lighting and focus."

    def _resolve_model_path(self, candidate: str) -> str:
        possible = [
            candidate,
            os.path.join(os.getcwd(), candidate),
            os.path.join(os.getcwd(), "models", os.path.basename(candidate)),
        ]
        for path in possible:
            if os.path.exists(path):
                return path
        return candidate

    # ------------------------------------------------------------------ #
    # Duplicate Detection (pHash)
    # ------------------------------------------------------------------ #
    def compute_phash(self, image_path: str, hash_size: int = 16) -> Dict:
        """
        Compute perceptual hash (pHash) for duplicate detection.
        
        pHash is robust against minor image modifications like resizing,
        compression, and slight color changes - making it ideal for
        detecting if the same item photo is being submitted multiple times.
        
        Args:
            image_path: Path to the image file
            hash_size: Size of the hash (default 16 for 256-bit hash)
            
        Returns:
            Dict containing:
                - phash: The perceptual hash as a hex string
                - dhash: Difference hash for additional comparison
                - valid: Whether hash computation succeeded
        """
        result = {
            "valid": False,
            "phash": None,
            "dhash": None,
            "feedback": ""
        }
        
        try:
            img = PILImage.open(image_path)
            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Compute perceptual hash (DCT-based)
            phash = imagehash.phash(img, hash_size=hash_size)
            result["phash"] = str(phash)
            
            # Also compute difference hash for robustness
            dhash = imagehash.dhash(img, hash_size=hash_size)
            result["dhash"] = str(dhash)
            
            result["valid"] = True
            result["feedback"] = "Image hash computed successfully"
            
            if self.enable_logging:
                logger.info(f"Computed pHash: {phash} for {image_path}")
                
        except Exception as e:
            result["feedback"] = f"Failed to compute image hash: {str(e)}"
            if self.enable_logging:
                logger.error(f"pHash computation failed: {e}")
                
        return result

    def check_duplicate(
        self,
        image_path: str,
        existing_hashes: List[str],
        threshold: int = 10
    ) -> Dict:
        """
        Check if an image is a duplicate of existing submissions.
        
        Uses Hamming distance between perceptual hashes to detect
        similar images. A lower threshold means stricter matching.
        
        Args:
            image_path: Path to the image to check
            existing_hashes: List of pHash hex strings to compare against
            threshold: Maximum Hamming distance to consider as duplicate
                      (0 = exact match, 10 = very similar, 20 = somewhat similar)
                      
        Returns:
            Dict containing:
                - is_duplicate: Whether a duplicate was found
                - similarity: Similarity score (1.0 = identical)
                - matched_hash: The matching hash if duplicate found
                - distance: Hamming distance to closest match
        """
        result = {
            "is_duplicate": False,
            "similarity": 0.0,
            "matched_hash": None,
            "distance": None,
            "feedback": ""
        }
        
        try:
            # Compute hash for current image
            hash_result = self.compute_phash(image_path)
            if not hash_result["valid"]:
                result["feedback"] = hash_result["feedback"]
                return result
                
            current_hash = imagehash.hex_to_hash(hash_result["phash"])
            
            min_distance = float('inf')
            best_match = None
            
            for existing_hex in existing_hashes:
                try:
                    existing_hash = imagehash.hex_to_hash(existing_hex)
                    distance = current_hash - existing_hash  # Hamming distance
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_match = existing_hex
                except Exception:
                    continue
            
            if best_match is not None:
                # Convert distance to similarity (assuming 256-bit hash)
                max_distance = 256  # Maximum possible Hamming distance
                similarity = 1 - (min_distance / max_distance)
                
                result["distance"] = min_distance
                result["similarity"] = round(similarity, 3)
                
                if min_distance <= threshold:
                    result["is_duplicate"] = True
                    result["matched_hash"] = best_match
                    result["feedback"] = f"Duplicate detected! Similarity: {similarity:.1%}"
                    
                    if self.enable_logging:
                        logger.warning(
                            f"Duplicate image detected: distance={min_distance}, "
                            f"similarity={similarity:.1%}"
                        )
                else:
                    result["feedback"] = "No duplicate found"
            else:
                result["feedback"] = "No existing hashes to compare against"
                
        except Exception as e:
            result["feedback"] = f"Duplicate check failed: {str(e)}"
            if self.enable_logging:
                logger.error(f"Duplicate check error: {e}")
                
        return result

    def batch_compute_hashes(self, image_paths: List[str]) -> List[Dict]:
        """
        Compute hashes for multiple images efficiently.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of hash result dictionaries
        """
        results = []
        for path in image_paths:
            result = self.compute_phash(path)
            result["image_path"] = path
            results.append(result)
        return results
    
    def _map_yolo_class(self, yolo_class: str) -> str:
        """
        Map YOLO's 80 COCO classes to Lost & Found categories.
        Uses comprehensive dictionary mapping for accuracy.
        """
        # Comprehensive YOLO to Lost & Found mapping
        YOLO_MAPPING = {
            # Electronics - Direct Mapping
            "cell phone": "phone",
            "laptop": "laptop",
            "mouse": "mouse",
            "keyboard": "keyboard",
            "remote": "remote",
            "tv": "electronics",
            
            # Personal Items - Bags & Accessories  
            "handbag": "wallet",  # Closest match - wallets often detected as handbag
            "backpack": "backpack",
            "suitcase": "luggage",
            "umbrella": "umbrella",
            "tie": "clothing",
            
            # Common Lost Items
            "book": "book",
            "bottle": "bottle",
            "cup": "cup",
            "clock": "clock",
            "scissors": "scissors",
            "teddy bear": "toy",
            
            # Sports Equipment
            "sports ball": "ball",
            "baseball bat": "sports_equipment",
            "baseball glove": "sports_equipment",
            "skateboard": "skateboard",
            "tennis racket": "sports_equipment",
            "bicycle": "bicycle",
            "surfboard": "sports_equipment",
            "skis": "sports_equipment",
            "snowboard": "sports_equipment",
            
            # Utensils
            "wine glass": "glass",
            "cup": "cup",
            "fork": "utensils",
            "knife": "utensils",
            "spoon": "utensils",
            "bowl": "bowl",
        }
        
        yolo_class_lower = yolo_class.lower()
        
        # Check direct mapping
        if yolo_class_lower in YOLO_MAPPING:
            return YOLO_MAPPING[yolo_class_lower]
        
        # For unmapped classes, keep original name
        # These will likely trigger ViT fallback if confidence is low
        return yolo_class

    
    def _generate_yolo_feedback(self, high_conf: List[Dict], all_detections: List[Dict]) -> str:
        """Generate helpful feedback for YOLO detections."""
        if not high_conf:
            if all_detections:
                top = all_detections[0]
                return f"Uncertain detection: possibly {top['class']} ({top['confidence']*100:.0f}% confidence)"
            return "No clear objects detected. Try retaking with better lighting."
        
        detected = high_conf[0]
        feedback = f"✓ Detected {detected['class']} ({detected['confidence']*100:.0f}% confidence)"
        
        if len(high_conf) > 1:
            feedback += f" and {len(high_conf)-1} other object(s)"
        
        return feedback

