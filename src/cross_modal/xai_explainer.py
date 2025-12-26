"""
Explainable AI (XAI) Module for Discrepancy Resolution
Part of Research-Grade Enhancement (Novel Contribution #4)

This module generates human-readable explanations for validation failures,
helping users understand WHY their input was rejected.
"""

import logging
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)

class XAIExplainer:
    """
    Generates explanations for cross-modal discrepancies.
    """
    
    def __init__(self):
        self.color_keywords = [
            "red", "blue", "green", "yellow", "black", "white", "brown",
            "gray", "grey", "orange", "purple", "pink", "silver", "gold"
        ]
        
    def generate_explanation(self,
                           image_result: Optional[Dict] = None,
                           text_result: Optional[Dict] = None,
                           voice_result: Optional[Dict] = None,
                           cross_modal_results: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive explanation for validation failures.
        
        Returns:
            {
                "has_discrepancy": bool,
                "discrepancy_type": str,  # "color", "object", "quantity", "context"
                "explanation": str,
                "severity": str,  # "low", "medium", "high"
                "suggestions": List[str]
            }
        """
        result = {
            "has_discrepancy": False,
            "discrepancy_type": None,
            "explanation": "",
            "severity": "low",
            "suggestions": []
        }
        
        # Check for object mismatch
        object_explanation = self._check_object_mismatch(image_result, text_result, voice_result)
        if object_explanation:
            result.update(object_explanation)
            return result
            
        # Check for color mismatch
        color_explanation = self._check_color_mismatch(image_result, text_result)
        if color_explanation:
            result.update(color_explanation)
            return result
            
        # Check for CLIP similarity issues
        if cross_modal_results and "image_text" in cross_modal_results:
            clip_result = cross_modal_results["image_text"]
            if not clip_result.get("valid", True):
                similarity = clip_result.get("similarity", 0)
                result["has_discrepancy"] = True
                result["discrepancy_type"] = "semantic_mismatch"
                result["severity"] = "high" if similarity < 0.5 else "medium"
                result["explanation"] = (
                    f"The image and description don't align well (similarity: {similarity:.0%}). "
                    f"Make sure your photo clearly shows the item you're describing."
                )
                result["suggestions"] = [
                    "Take a clearer photo of the item",
                    "Ensure your description matches what's in the photo",
                    "Try describing the item's most visible features"
                ]
                return result
        
        # Check voice-text consistency
        if cross_modal_results and "voice_text" in cross_modal_results:
            voice_text = cross_modal_results["voice_text"]
            if not voice_text.get("valid", True):
                result["has_discrepancy"] = True
                result["discrepancy_type"] = "voice_text_mismatch"
                result["severity"] = "medium"
                result["explanation"] = (
                    "Your voice description doesn't match your written description. "
                    "They should describe the same item."
                )
                result["suggestions"] = [
                    "Re-record your voice description",
                    "Update your text to match what you said",
                    "Speak more clearly when recording"
                ]
                return result
        
        return result
    
    def _check_object_mismatch(self,
                              image_result: Optional[Dict],
                              text_result: Optional[Dict],
                              voice_result: Optional[Dict]) -> Optional[Dict]:
        """Check if detected object differs from described object."""
        if not image_result or not text_result:
            return None
            
        # Extract detected object from image
        detected_class = None
        if "detection" in image_result:
            detection = image_result["detection"]
            if "class" in detection:
                detected_class = detection["class"]
            elif "predicted_class" in detection:
                detected_class = detection["predicted_class"]
                
        if not detected_class:
            return None
            
        # Extract described object from text
        text_body = text_result.get("text", "").lower()
        entities = text_result.get("entities", {})
        item_mentions = entities.get("item_mentions", [])
        
        # Simple object comparison
        detected_lower = detected_class.lower()
        
        # Check if detected class is mentioned in text
        is_mentioned = (
            detected_lower in text_body or
            any(detected_lower in item.lower() for item in item_mentions)
        )
        
        if not is_mentioned and item_mentions:
            # Found mismatch
            described_item = item_mentions[0] if item_mentions else "unknown"
            return {
                "has_discrepancy": True,
                "discrepancy_type": "object_mismatch",
                "severity": "high",
                "explanation": (
                    f"Object mismatch detected: The image shows a '{detected_class}' "
                    f"but you described a '{described_item}'. "
                    f"Please ensure the photo matches your description."
                ),
                "suggestions": [
                    f"Upload a photo of the {described_item} instead",
                    f"Update your description to '{detected_class}' if that's what you meant",
                    "Double-check you're describing the correct item"
                ]
            }
            
        return None
    
    def _check_color_mismatch(self,
                            image_result: Optional[Dict],
                            text_result: Optional[Dict]) -> Optional[Dict]:
        """Check if image color differs from described color."""
        if not image_result or not text_result:
            return None
            
        # Extract colors from text
        text_body = text_result.get("text", "").lower()
        entities = text_result.get("entities", {})
        text_colors = entities.get("color_mentions", [])
        
        # Also extract from text body directly
        for color in self.color_keywords:
            if color in text_body and color not in text_colors:
                text_colors.append(color)
                
        if not text_colors:
            return None  # No color mentioned, can't check
            
        # Extract dominant color from image (if available)
        image_color = None
        if "dominant_color" in image_result:
            image_color = image_result["dominant_color"]
        elif "quality" in image_result and "dominant_color" in image_result["quality"]:
            image_color = image_result["quality"]["dominant_color"]
            
        if not image_color:
            return None
            
        # Compare colors
        image_color_lower = image_color.lower()
        if image_color_lower not in [c.lower() for c in text_colors]:
            return {
                "has_discrepancy": True,
                "discrepancy_type": "color_mismatch",
                "severity": "medium",
                "explanation": (
                    f"Color mismatch detected: The image appears to be {image_color}, "
                    f"but you described it as {', '.join(text_colors)}. "
                    f"Color accuracy helps match your item faster."
                ),
                "suggestions": [
                    f"Update description to mention '{image_color}' color",
                    "Take photo in better lighting if color looks wrong",
                    "Verify you're describing the correct item"
                ]
            }
            
        return None
    
    def get_summary_message(self, explanation_result: Dict) -> str:
        """
        Generate a user-friendly summary message.
        """
        if not explanation_result.get("has_discrepancy"):
            return "✓ All inputs are consistent."
            
        severity = explanation_result.get("severity", "low")
        emoji = "⚠️" if severity == "medium" else "❌" if severity == "high" else "ℹ️"
        
        return f"{emoji} {explanation_result.get('explanation', 'Discrepancy detected.')}"
