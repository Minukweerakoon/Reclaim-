"""
Alert Generation and Management Utilities
"""

from typing import List, Dict
import json
import csv
from datetime import datetime


class AlertManager:
    """Manages alert generation and storage"""
    
    @staticmethod
    def format_alert(alert: Dict, camera_id: str = None) -> Dict:
        """
        Format alert for API response
        
        Args:
            alert: Raw alert dictionary
            camera_id: Optional camera identifier
            
        Returns:
            Formatted alert dictionary
        """
        formatted = {
            "alert_id": f"{alert.get('type', 'UNKNOWN')}_{alert.get('frame', 0)}_{alert.get('timestamp', 0)}",
            "type": alert.get("type", "UNKNOWN"),
            "timestamp": alert.get("timestamp", datetime.now().timestamp()),
            "frame": alert.get("frame", 0) or alert.get("frame_number", 0),
            "severity": AlertManager._get_severity(alert.get("type", "")),
            "details": {},
            "frame_image": alert.get("frame_image"),  # Filename of captured frame (exact frame when alert triggered)
        }
        
        if camera_id:
            formatted["camera_id"] = camera_id
        
        # Add type-specific details
        alert_type = alert.get("type", "")
        if alert_type == "BAG_UNATTENDED":
            formatted["details"] = {
                "bag_id": alert.get("bag_id"),
                "item_type": alert.get("item_type", "bag"),
                "bag_bbox": alert.get("bag_bbox"),
                "duration_seconds": alert.get("duration_seconds", 0)
            }
        elif alert_type == "LOITER_NEAR_UNATTENDED":
            formatted["details"] = {
                "person_id": alert.get("person_id"),
                "bag_id": alert.get("bag_id"),
                "item_type": alert.get("item_type", "bag"),
                "person_bbox": alert.get("person_bbox"),
                "bag_bbox": alert.get("bag_bbox"),
                "dwell_time_seconds": alert.get("dwell_time_seconds", 0)
            }
        elif alert_type == "RUNNING":
            formatted["details"] = {
                "person_id": alert.get("person_id"),
                "person_bbox": alert.get("person_bbox"),
                "speed": alert.get("speed", 0)
            }
        elif alert_type == "OWNER_RETURNED":
            formatted["details"] = {
                "bag_id": alert.get("bag_id"),
                "item_type": alert.get("item_type", "bag"),
                "person_id": alert.get("person_id"),
                "bag_bbox": alert.get("bag_bbox"),
                "distance_px": alert.get("distance_px", 0)
            }
        
        return formatted
    
    @staticmethod
    def _get_severity(alert_type: str) -> str:
        """Get severity level for alert type"""
        severity_map = {
            "BAG_UNATTENDED": "MEDIUM",
            "LOITER_NEAR_UNATTENDED": "HIGH",
            "RUNNING": "LOW",
            "OWNER_RETURNED": "INFO"
        }
        return severity_map.get(alert_type, "UNKNOWN")
    
    @staticmethod
    def save_alerts_to_json(alerts: List[Dict], output_path: str):
        """
        Save alerts to JSON file
        
        Args:
            alerts: List of alert dictionaries
            output_path: Output file path
        """
        formatted_alerts = [AlertManager.format_alert(alert) for alert in alerts]
        
        with open(output_path, 'w') as f:
            json.dump(formatted_alerts, f, indent=2)
    
    @staticmethod
    def save_alerts_to_csv(alerts: List[Dict], output_path: str):
        """
        Save alerts to CSV file
        
        Args:
            alerts: List of alert dictionaries
            output_path: Output file path
        """
        if not alerts:
            return
        
        formatted_alerts = [AlertManager.format_alert(alert) for alert in alerts]
        
        # Get all unique keys from all alerts
        all_keys = set()
        for alert in formatted_alerts:
            all_keys.update(alert.keys())
            if "details" in alert and isinstance(alert["details"], dict):
                all_keys.update([f"details.{k}" for k in alert["details"].keys()])
        
        # Flatten details
        rows = []
        for alert in formatted_alerts:
            row = {k: alert.get(k, "") for k in all_keys if k != "details"}
            if "details" in alert and isinstance(alert["details"], dict):
                for k, v in alert["details"].items():
                    row[f"details.{k}"] = v
            rows.append(row)
        
        # Write CSV
        if rows:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(rows)

