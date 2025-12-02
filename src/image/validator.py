import os
import time
import logging
from typing import Dict, List, Optional

import cv2
import numpy as np
import torch
from ultralytics import YOLO

logger = logging.getLogger("ImageValidator")
logger.setLevel(logging.INFO)


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
    ) -> None:
        self.enable_logging = enable_logging
        self.model_path = self._resolve_model_path(model_path or "yolov8n.pt")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(self.model_path)
        if self.enable_logging:
            logger.info("Loaded YOLO model %s on %s", self.model_path, self.device)

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.profile_face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_profileface.xml"
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def validate_image(self, image_path: str) -> Dict:
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
        objects_result = self.detect_objects(image_path)
        privacy_result = self.detect_privacy_content(image_path)

        sharpness_score = sharpness_result["score"] / 100
        detection_score = objects_result["detection_score"] / 100
        overall = (sharpness_score * 0.6 + detection_score * 0.4) * 100
        is_valid = overall >= 70

        return {
            "valid": is_valid,
            "overall_score": round(overall, 1),
            "sharpness": sharpness_result,
            "objects": objects_result,
            "privacy": privacy_result,
            "feedback": self._generate_feedback(sharpness_result, objects_result, overall),
            "processing_time": round(time.time() - start, 3),
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

    def detect_objects(self, image_path: str) -> Dict:
        results = self.model(image_path, conf=0.3, device=self.device, verbose=False)
        detections: List[Dict] = []
        for result in results:
            if not result.boxes:
                continue
            for box in result.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                class_name = result.names.get(cls_id, "object")
                detections.append(
                    {
                        "class": class_name,
                        "confidence": round(conf, 3),
                        "bbox": [float(x) for x in box.xyxy[0].tolist()],
                    }
                )

        detections.sort(key=lambda x: x["confidence"], reverse=True)
        high_conf = [d for d in detections if d["confidence"] > 0.5]
        detection_score = min(100, len(high_conf) * 50)
        return {
            "valid": len(high_conf) > 0,
            "detections": detections[:3],
            "detection_score": detection_score,
            "feedback": f"Detected {len(detections)} objects"
            if detections
            else "No clear objects detected",
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

