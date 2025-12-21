"""
Video Processing Utilities
Handles video file reading, writing, and frame extraction
"""

import cv2
import os
from typing import List, Tuple, Optional
import numpy as np


class VideoProcessor:
    """Utility class for video processing"""
    
    @staticmethod
    def get_video_info(video_path: str) -> dict:
        """
        Get video information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info (fps, width, height, frame_count)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        cap.release()
        
        return {
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "duration_seconds": frame_count / fps if fps > 0 else 0
        }
    
    @staticmethod
    def read_video(video_path: str, max_frames: Optional[int] = None) -> Tuple[List[np.ndarray], dict]:
        """
        Read video and extract frames
        
        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to read (None for all)
            
        Returns:
            Tuple of (frames list, video info dict)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames.append(frame)
            frame_count += 1
            
            if max_frames and frame_count >= max_frames:
                break
        
        cap.release()
        
        info = {
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": len(frames)
        }
        
        return frames, info
    
    @staticmethod
    def write_video(
        frames: List[np.ndarray],
        output_path: str,
        fps: float = 30.0,
        codec: str = "mp4v"
    ) -> str:
        """
        Write frames to video file
        
        Args:
            frames: List of frames as numpy arrays
            output_path: Output video file path
            fps: Frames per second
            codec: Video codec (e.g., 'mp4v', 'XVID')
            
        Returns:
            Path to output video
        """
        if len(frames) == 0:
            raise ValueError("No frames to write")
        
        height, width = frames[0].shape[:2]
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in frames:
            out.write(frame)
        
        out.release()
        
        return output_path
    
    @staticmethod
    def draw_detections(
        frame: np.ndarray,
        detections: List[dict],
        draw_track_ids: bool = True
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: Input frame
            detections: List of detection dictionaries
            draw_track_ids: Whether to draw track IDs
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        for det in detections:
            bbox = det.get("bbox", [])
            if len(bbox) != 4:
                continue
            
            x1, y1, x2, y2 = map(int, bbox)
            class_name = det.get("class_name", "unknown")
            confidence = det.get("confidence", 0.0)
            track_id = det.get("track_id")
            
            # Choose color based on class
            if class_name == "bag":
                color = (0, 255, 255)  # Yellow
            elif class_name == "person":
                color = (0, 255, 0)  # Green
            else:
                color = (255, 0, 0)  # Blue
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label
            label = f"{class_name} {confidence:.2f}"
            if draw_track_ids and track_id is not None:
                label += f" ID:{track_id}"
            
            # Draw label background
            (label_width, label_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                annotated_frame,
                (x1, y1 - label_height - 10),
                (x1 + label_width, y1),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                annotated_frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1
            )
        
        return annotated_frame
    
    @staticmethod
    def draw_alerts(
        frame: np.ndarray,
        alerts: List[dict]
    ) -> np.ndarray:
        """
        Draw alert indicators on frame
        
        Args:
            frame: Input frame
            alerts: List of alert dictionaries
            
        Returns:
            Annotated frame with alerts
        """
        annotated_frame = frame.copy()
        
        for alert in alerts:
            alert_type = alert.get("type", "")
            
            if alert_type == "BAG_UNATTENDED":
                bag_bbox = alert.get("bag_bbox", [])
                if len(bag_bbox) == 4:
                    x1, y1, x2, y2 = map(int, bag_bbox)
                    # Draw red border for unattended bag
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(
                        annotated_frame,
                        "UNATTENDED BAG",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )
            
            elif alert_type == "LOITER_NEAR_UNATTENDED":
                person_bbox = alert.get("person_bbox", [])
                if len(person_bbox) == 4:
                    x1, y1, x2, y2 = map(int, person_bbox)
                    # Draw orange border for loitering
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 165, 255), 3)
                    cv2.putText(
                        annotated_frame,
                        "LOITERING",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 165, 255),
                        2
                    )
        
        return annotated_frame

