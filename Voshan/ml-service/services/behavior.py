"""
Behavior Detection Service
Detects suspicious behaviors: unattended bags, loitering, running
Extracted and refactored from original YOLOv8/YOLOv11 notebooks
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
import math
from collections import defaultdict, deque
import time


class BehaviorDetector:
    """Detects suspicious behaviors based on tracked objects"""
    
    def __init__(
        self,
        owner_max_dist: float = 120,
        owner_absent_sec: float = 20,
        loiter_near_radius: float = 70,
        loiter_near_sec: float = 20,
        running_speed: float = 260,
        fps: float = 30.0,
        item_class_names: Optional[List[str]] = None,
    ):
        """
        Initialize behavior detector
        
        Args:
            owner_max_dist: Max distance (pixels) for bag to be considered "attended"
            owner_absent_sec: Time (seconds) before bag is marked "unattended"
            loiter_near_radius: Radius (pixels) for loitering detection near unattended bag
            loiter_near_sec: Time (seconds) person must stay to trigger loitering alert
            running_speed: Speed threshold (pixels/second) for running detection
            fps: Frames per second of video
            item_class_names: Class names treated as "items" (unattended/loitering). Default ["bag"].
        """
        self.owner_max_dist = owner_max_dist
        self.owner_absent_sec = owner_absent_sec
        self.loiter_near_radius = loiter_near_radius
        self.loiter_near_sec = loiter_near_sec
        self.running_speed = running_speed
        self.fps = fps
        self._item_class_set = set((c or "").strip().lower() for c in (item_class_names or ["bag"]) if c)

        # State tracking
        self.bag_owner_lastseen = defaultdict(float)
        self.bag_center = {}
        self.item_type_by_id = {}  # item_id -> class_name (e.g. "bag", "handbag")
        self.unattended_bags = set()
        
        # Person tracking
        self.person_pos_hist = defaultdict(lambda: deque(maxlen=int(fps * 5)))  # Short history for speed calculation
        
        # Loitering tracking
        self.near_unattend_start = defaultdict(lambda: defaultdict(float))  # person_id -> bag_id -> start time
        
        # Interaction-with-bag alert throttle (person_id -> bag_id -> last emit time)
        self._last_interaction_alert = defaultdict(lambda: defaultdict(float))
        
        # Frame tracking
        self.frame_count = 0
        self.current_time = 0.0  # Current time in seconds
        
        # Alerts
        self.alerts = []
    
    def calculate_distance(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate distance between centers of two bounding boxes"""
        center1_x = (bbox1[0] + bbox1[2]) / 2
        center1_y = (bbox1[1] + bbox1[3]) / 2
        center2_x = (bbox2[0] + bbox2[2]) / 2
        center2_y = (bbox2[1] + bbox2[3]) / 2
        
        dx = center2_x - center1_x
        dy = center2_y - center1_y
        return np.sqrt(dx**2 + dy**2)
    
    def get_bbox_center(self, bbox: List[float]) -> Tuple[float, float]:
        """Get center point of bounding box"""
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        return (center_x, center_y)
    
    def process_frame(self, tracked_objects: List[Dict], current_time: Optional[float] = None) -> List[Dict]:
        """
        Process a frame and detect behaviors
        Matches the logic from original YOLOv8/YOLOv11 notebooks
        
        Args:
            tracked_objects: List of tracked objects from tracker
            current_time: Current time in seconds (if None, calculated from frame_count)
            
        Returns:
            List of alerts/events detected in this frame
        """
        self.frame_count += 1
        
        # Calculate current time
        if current_time is not None:
            self.current_time = current_time
        else:
            self.current_time = self.frame_count / self.fps
        
        frame_alerts = []
        
        # Separate people and items by configurable class names (supports bag + handbag, backpack, suitcase, etc.)
        people = {}   # person_id -> (center_x, center_y, bbox)
        bags = {}     # item_id -> (center_x, center_y, bbox, item_type)
        
        for obj in tracked_objects:
            track_id = obj.get("track_id")
            if track_id is None:
                continue
            
            class_name = (obj.get("class_name") or "").strip().lower()
            bbox = obj.get("bbox", [])
            if len(bbox) != 4:
                continue
            
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            if class_name == "person":
                people[track_id] = (center_x, center_y, bbox)
            elif class_name in self._item_class_set:
                bags[track_id] = (center_x, center_y, bbox, class_name)
                self.item_type_by_id[track_id] = class_name
        
        # === Unattended Item Detection ===
        for bag_id, bag_data in bags.items():
            bag_cx, bag_cy, bag_bbox, item_type = bag_data[0], bag_data[1], bag_data[2], bag_data[3]
            self.bag_center[bag_id] = (bag_cx, bag_cy)
            
            # Find nearest person to the bag
            nearest_person_id = None
            min_dist = float('inf')
            
            for person_id, (person_cx, person_cy, _) in people.items():
                dist = math.hypot(bag_cx - person_cx, bag_cy - person_cy)
                if dist < min_dist:
                    nearest_person_id = person_id
                    min_dist = dist
            
            # Check if owner is nearby
            if nearest_person_id is not None and min_dist <= self.owner_max_dist:
                # Owner is nearby
                self.bag_owner_lastseen[bag_id] = self.current_time
                
                # If bag was unattended and owner returned, log event
                if bag_id in self.unattended_bags:
                    self.unattended_bags.discard(bag_id)
                    alert = {
                        "type": "OWNER_RETURNED",
                        "bag_id": bag_id,
                        "item_type": item_type,
                        "person_id": nearest_person_id,
                        "bag_bbox": bag_bbox,
                        "distance_px": round(min_dist, 1),
                        "frame": self.frame_count,
                        "timestamp": time.time()
                    }
                    frame_alerts.append(alert)
                    self.alerts.append(alert)
            else:
                # No owner nearby
                # Initialize last seen time if this is first time seeing the bag
                if bag_id not in self.bag_owner_lastseen:
                    self.bag_owner_lastseen[bag_id] = self.current_time
                
                # Check if bag should be marked as unattended
                sec_since_owner = self.current_time - self.bag_owner_lastseen[bag_id]
                if sec_since_owner >= self.owner_absent_sec:
                    if bag_id not in self.unattended_bags:
                        self.unattended_bags.add(bag_id)
                        alert = {
                            "type": "BAG_UNATTENDED",
                            "bag_id": bag_id,
                            "item_type": item_type,
                            "bag_bbox": bag_bbox,
                            "duration_seconds": sec_since_owner,
                            "frame": self.frame_count,
                            "timestamp": time.time()
                        }
                        frame_alerts.append(alert)
                        self.alerts.append(alert)
        
        # === Loitering Detection Near Unattended Bags ===
        for person_id, (person_cx, person_cy, person_bbox) in people.items():
            # Distance to nearest bag (any item) - if within range, suppress false RUNNING (e.g. bending over bag)
            min_dist_to_bag = float('inf')
            nearest_bag_id = None
            nearest_bag_data = None
            for bag_id, bag_data in bags.items():
                bag_cx, bag_cy = bag_data[0], bag_data[1]
                d = math.hypot(person_cx - bag_cx, person_cy - bag_cy)
                if d < min_dist_to_bag:
                    min_dist_to_bag = d
                    nearest_bag_id = bag_id
                    nearest_bag_data = bag_data
            
            person_near_bag = min_dist_to_bag <= self.owner_max_dist
            
            # When person is near a bag, emit INTERACTION_WITH_BAG (throttled to once per 2 sec per person-bag pair)
            if person_near_bag and nearest_bag_id is not None and nearest_bag_data is not None:
                last_emit = self._last_interaction_alert[person_id][nearest_bag_id]
                if self.current_time - last_emit >= 2.0:
                    bag_cx, bag_cy, bag_bbox, item_type = nearest_bag_data
                    alert = {
                        "type": "INTERACTION_WITH_BAG",
                        "person_id": person_id,
                        "bag_id": nearest_bag_id,
                        "item_type": item_type,
                        "person_bbox": person_bbox,
                        "bag_bbox": bag_bbox,
                        "distance_px": round(min_dist_to_bag, 1),
                        "frame": self.frame_count,
                        "timestamp": time.time()
                    }
                    frame_alerts.append(alert)
                    self.alerts.append(alert)
                    self._last_interaction_alert[person_id][nearest_bag_id] = self.current_time
            
            # Track person position history for speed calculation
            hist = self.person_pos_hist[person_id]
            if hist:
                # Calculate speed (for running detection)
                x0, y0 = hist[-1]
                speed = math.hypot(person_cx - x0, person_cy - y0) * self.fps
                
                # Detect running ONLY when person is NOT near a bag (bending over a bag causes centroid jump → false running)
                if not person_near_bag and speed > self.running_speed:
                    alert = {
                        "type": "RUNNING",
                        "person_id": person_id,
                        "person_bbox": person_bbox,
                        "speed": round(speed, 1),
                        "frame": self.frame_count,
                        "timestamp": time.time()
                    }
                    frame_alerts.append(alert)
                    self.alerts.append(alert)
            
            hist.append((person_cx, person_cy))
            
            # Check loitering near unattended bags
            for bag_id in list(self.unattended_bags):
                bag_cx, bag_cy = self.bag_center.get(bag_id, (None, None))
                if bag_cx is None:
                    continue
                
                # Calculate distance to unattended bag
                dist = math.hypot(person_cx - bag_cx, person_cy - bag_cy)
                
                if dist <= self.loiter_near_radius:
                    # Person is near unattended bag
                    if self.near_unattend_start[person_id][bag_id] == 0.0:
                        # Start loitering timer
                        self.near_unattend_start[person_id][bag_id] = self.current_time
                    
                    # Check if loitering long enough
                    dwell_time = self.current_time - self.near_unattend_start[person_id][bag_id]
                    if dwell_time >= self.loiter_near_sec:
                        bag_bbox = bags.get(bag_id, (None, None, [], ""))[2] if bag_id in bags else []
                        item_type = self.item_type_by_id.get(bag_id, "item")
                        alert = {
                            "type": "LOITER_NEAR_UNATTENDED",
                            "person_id": person_id,
                            "bag_id": bag_id,
                            "item_type": item_type,
                            "person_bbox": person_bbox,
                            "bag_bbox": bag_bbox,
                            "dwell_time_seconds": round(dwell_time, 1),
                            "frame": self.frame_count,
                            "timestamp": time.time()
                        }
                        frame_alerts.append(alert)
                        self.alerts.append(alert)
                        # Reset timer to avoid duplicate alerts (only log once per loitering event)
                        self.near_unattend_start[person_id][bag_id] = self.current_time
                else:
                    # Person moved away, reset timer
                    self.near_unattend_start[person_id][bag_id] = 0.0
        
        return frame_alerts
    
    def get_all_alerts(self) -> List[Dict]:
        """Get all alerts generated so far"""
        return self.alerts
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []
    
    def reset(self):
        """Reset all state"""
        self.bag_owner_lastseen = defaultdict(float)
        self.bag_center = {}
        self.item_type_by_id = {}
        self.unattended_bags = set()
        self.person_pos_hist = defaultdict(lambda: deque(maxlen=int(self.fps * 5)))
        self.near_unattend_start = defaultdict(lambda: defaultdict(float))
        self._last_interaction_alert = defaultdict(lambda: defaultdict(float))
        self.frame_count = 0
        self.current_time = 0.0
        self.alerts = []
    
    def get_unattended_bags(self) -> set:
        """Get set of currently unattended bag IDs"""
        return self.unattended_bags.copy()

