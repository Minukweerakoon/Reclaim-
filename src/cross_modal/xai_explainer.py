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
                           cross_modal_results: Optional[Dict] = None,
                           description: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Get description from various sources
        desc_text = description or ""
        if not desc_text and text_result:
            desc_text = text_result.get("text", "") or text_result.get("description", "")
        if not desc_text and cross_modal_results:
            # Try to get from image_text result
            image_text = cross_modal_results.get("image_text", {})
            desc_text = image_text.get("text", "") or image_text.get("description", "")
        
        desc_lower = desc_text.lower()
        
        # Extract colors mentioned in description
        mentioned_colors = [c for c in self.color_keywords if c in desc_lower]
        
        # Get detected object from image
        detected_object = None
        if image_result:
            objects = image_result.get("objects", {})
            detections = objects.get("detections", [])
            if detections and len(detections) > 0:
                detected_object = detections[0].get("class", detections[0].get("label", ""))
        
        # Check for object type mismatch
        object_mismatch = self._check_object_type_mismatch(detected_object, desc_lower)
        if object_mismatch:
            result.update(object_mismatch)
            return result
            
        # Check for color mismatch - if user mentioned blue but image likely shows different color
        if mentioned_colors:
            # Get image dominant color (if available in results)
            image_color = None
            if image_result:
                image_color = image_result.get("dominant_color")
                if not image_color and "quality" in image_result:
                    image_color = image_result["quality"].get("dominant_color")
            
            # If we have both image color and mentioned colors, check mismatch
            if image_color:
                image_color_lower = image_color.lower()
                if image_color_lower not in [c.lower() for c in mentioned_colors]:
                    return {
                        "has_discrepancy": True,
                        "discrepancy_type": "color_mismatch",
                        "severity": "medium",
                        "explanation": (
                            f"Color mismatch: You described '{', '.join(mentioned_colors)}' "
                            f"but the image appears to be {image_color}."
                        ),
                        "suggestions": [
                            f"Update your description to match the actual color ({image_color})",
                            "Upload a photo of the correct item",
                            "Take a clearer photo with better lighting"
                        ]
                    }
            
            # Even without dominant_color, note the colors mentioned for context
            result["mentioned_colors"] = mentioned_colors
            
        # Check for CLIP similarity issues (semantic mismatch)
        if cross_modal_results and "image_text" in cross_modal_results:
            clip_result = cross_modal_results["image_text"]
            similarity = clip_result.get("similarity", 1.0)
            if not clip_result.get("valid", True) or similarity < 0.85:
                # Create smart explanation based on what we know
                explanation_parts = []
                
                if detected_object and detected_object.lower() not in desc_lower:
                    explanation_parts.append(
                        f"The image shows '{detected_object}' which may not match your description"
                    )
                
                if mentioned_colors:
                    explanation_parts.append(
                        f"You mentioned '{', '.join(mentioned_colors)}' colors"
                    )
                
                if not explanation_parts:
                    explanation_parts.append(
                        "The image content doesn't match the description well"
                    )
                
                result["has_discrepancy"] = True
                result["discrepancy_type"] = "semantic_mismatch"
                result["severity"] = "high" if similarity < 0.5 else "medium"
                result["explanation"] = (
                    f"Low similarity ({similarity:.0%}): {'. '.join(explanation_parts)}. "
                    f"Please verify the photo matches your description."
                )
                result["suggestions"] = [
                    "Ensure the photo clearly shows the item you described",
                    "Update description to match what's in the photo",
                    "Take a clearer, well-lit photo of the item"
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
    
    def _check_object_type_mismatch(self, detected_object: Optional[str], description_lower: str) -> Optional[Dict]:
        """
        Check if detected object type doesn't match what user described.
        Works with simple string matching for common item types.
        """
        if not detected_object or not description_lower:
            return None
        
        detected_lower = detected_object.lower()
        
        # Common item type mappings (what YOLO detects -> what user might describe)
        item_aliases = {
            "luggage": ["suitcase", "luggage", "bag", "travel bag"],
            "backpack": ["backpack", "bag", "school bag", "rucksack"],
            "handbag": ["handbag", "purse", "bag"],
            "suitcase": ["suitcase", "luggage", "travel bag"],
            "umbrella": ["umbrella"],
            "cell phone": ["phone", "mobile", "smartphone", "cell phone"],
            "laptop": ["laptop", "notebook", "computer"],
            "wallet": ["wallet", "billfold"],
            "watch": ["watch", "wristwatch"],
            "glasses": ["glasses", "spectacles", "eyeglasses", "sunglasses"],
            "keys": ["keys", "key"],
        }
        
        # Find what user described
        described_item = None
        for item_type in ["backpack", "bag", "phone", "wallet", "laptop", "umbrella", 
                          "suitcase", "luggage", "watch", "glasses", "keys"]:
            if item_type in description_lower:
                described_item = item_type
                break
        
        if not described_item:
            return None  # Can't determine what user described
        
        # Check if detected object is compatible with description
        compatible = False
        for detected_type, aliases in item_aliases.items():
            if detected_lower in detected_type or detected_type in detected_lower:
                if any(alias in description_lower for alias in aliases):
                    compatible = True
                    break
        
        # Also check direct match
        if described_item in detected_lower or detected_lower in described_item:
            compatible = True
        
        if not compatible and detected_lower != described_item:
            return {
                "has_discrepancy": True,
                "discrepancy_type": "object_mismatch",
                "severity": "high",
                "explanation": (
                    f"Object mismatch: You described a '{described_item}' but the image "
                    f"shows a '{detected_object}'. Please verify you uploaded the correct photo."
                ),
                "suggestions": [
                    f"Upload a photo of your {described_item}",
                    f"Update your description to match '{detected_object}'",
                    "Verify you're describing the correct item"
                ]
            }
        
        return None
    
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
