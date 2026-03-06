"""
COCO Extension Service
Adds COCO-pretrained item classes without retraining: handbag, backpack, suitcase,
cell phone, laptop, tv, etc. Your custom model keeps bag + person; this runs a
second COCO model and merges detections.
"""

import os
from typing import List, Dict, Optional
import numpy as np
from ultralytics import YOLO


class CocoExtension:
    """
    Runs a COCO-pretrained YOLO to detect extra item classes (e.g. handbag, backpack,
    suitcase, cell phone, laptop, tv). Use with merged tracked_objects so one pipeline
    gets both custom (bag, person) and COCO items.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        item_class_names: Optional[List[str]] = None,
        confidence: float = 0.25,
        track_id_offset: int = 100000,
        device: str = "cuda:0",
    ):
        """
        Args:
            model_path: Path to .pt model (e.g. "yolo11n.pt"). If None, uses "yolo11n.pt" (downloads if needed).
            item_class_names: COCO class names to keep (e.g. ["handbag", "backpack", "suitcase"]).
            confidence: Detection confidence threshold.
            track_id_offset: Add this to COCO track IDs to avoid collision with custom model IDs.
            device: "cuda:0" or "cpu".
        """
        import torch
        self.device = device if torch.cuda.is_available() and "cuda" in device else "cpu"
        self.item_class_names = set((str(c).strip().lower() for c in (item_class_names or []) if c))
        self.confidence = confidence
        self.track_id_offset = track_id_offset

        path = model_path or "yolo11n.pt"
        if not os.path.isabs(path) and not os.path.exists(path):
            path = model_path or "yolo11n.pt"
        print(f"Loading COCO extension model: {path}")
        self.model = YOLO(path)
        self.model.to(self.device)
        print(f"COCO extension loaded on {self.device}, item_class_names={list(self.item_class_names)}")

    def track(self, frame: np.ndarray, persist: bool = True) -> List[Dict]:
        """
        Run COCO model tracking on frame, return only detections whose class_name
        is in item_class_names, with track_id offset so they don't collide with main model.
        """
        if not self.item_class_names:
            return []

        try:
            results = self.model.track(
                frame,
                persist=persist,
                verbose=False,
                conf=self.confidence,
                device=self.device,
            )
        except Exception:
            return []

        out = []
        if not results or results[0].boxes is None:
            return out

        boxes = results[0].boxes
        has_id = boxes.id is not None

        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].cpu().numpy())
            names = self.model.names
            if isinstance(names, dict):
                cls_name = names.get(cls_id, "")
            else:
                cls_name = names[cls_id] if cls_id < len(names) else ""
            cls_name = str(cls_name).strip().lower()
            if cls_name not in self.item_class_names:
                continue

            box = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            track_id = int(boxes.id[i].cpu().numpy()) + self.track_id_offset if has_id else None

            out.append({
                "track_id": track_id,
                "bbox": box.tolist(),
                "confidence": conf,
                "class_id": cls_id,
                "class_name": cls_name,
            })
        return out

    def get_model_info(self) -> Dict:
        return {
            "model_type": "coco_extension",
            "item_class_names": list(self.item_class_names),
            "track_id_offset": self.track_id_offset,
            "device": self.device,
        }
