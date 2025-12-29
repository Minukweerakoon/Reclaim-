"""
Enhanced XAI Explainer - Phase 2
Adds multi-dimensional discrepancy detection and SHAP integration
"""

import logging
import re
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


def _extract_brands(text: str) -> List[str]:
    """Extract brand names from text using common brand patterns."""
    common_brands = [
        "apple", "samsung", "nike", "adidas", "sony", "dell", "hp", "lenovo",
        "asus", "acer", "microsoft", "google", "amazon", "canon", "nikon",
        "gucci", "prada", "louis vuitton", "coach", "michael kors"
    ]
    
    text_lower = text.lower()
    found_brands = [brand for brand in common_brands if brand in text_lower]
    
    # Also check for capitalized words (likely brand names)
    words = text.split()
    capitalized = [w for w in words if w and w[0].isupper() and len(w) > 2]
    
    return list(set(found_brands + [c.lower() for c in capitalized if c.lower() not in common_brands]))


def _extract_condition(text: str) -> Optional[str]:
    """Extract condition descriptors from text."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["new", "brand new", "unused", "mint"]):
        return "new"
    elif any(word in text_lower for word in ["used", "old", "worn", "damaged", "broken"]):
        return "used"
    elif any(word in text_lower for word in ["good condition", "excellent", "like new"]):
        return "good"
    
    return None


def check_brand_mismatch(
    image_result: Optional[Dict],
    text_result: Optional[Dict]
) -> Dict[str, Any]:
    """
    Detect brand mentions in text not visible in image.
    
    Returns discrepancy dict if mismatch found.
    """
    if not image_result or not text_result:
        return {"has_mismatch": False}
    
    text = text_result.get("text", "")
    text_brands = _extract_brands(text)
    
    if not text_brands:
        return {"has_mismatch": False}
    
    # Check if image has OCR text (if available)
    image_text_ocr = image_result.get("ocr_text", "")
    if not image_text_ocr:
        # Try to get from detections
        detections = image_result.get("objects", {}).get("detections", [])
        for detection in detections:
            if "text" in detection:
                image_text_ocr += " " + detection["text"]
    
    # Check which brands are not in image
    missing_brands = [
        brand for brand in text_brands
        if brand.lower() not in image_text_ocr.lower()
    ]
    
    if missing_brands and len(missing_brands) > 0:
        brands_formatted = ', '.join([f"'{b}'" for b in missing_brands])
        return {
            "has_mismatch": True,
            "severity": "medium",
            "explanation": (
                f"Brand mismatch: You mentioned {brands_formatted} "
                f"but these brands are not clearly visible in the image. "
                f"Brand logos help verify authenticity."
            ),
            "suggestions": [
                "Include a clear photo of the brand logo or label",
                "Mention exact model/product name if brand not visible",
                "Verify the brand is correct"
            ]
        }
    
    return {"has_mismatch": False}


def check_location_consistency(
    text_result: Optional[Dict],
    voice_result: Optional[Dict]
) -> Dict[str, Any]:
    """
    Check if location mentioned in text matches voice description.
    """
    if not text_result or not voice_result:
        return {"has_mismatch": False}
    
    text = text_result.get("text", "").lower()
    voice_transcription = voice_result.get("transcription", {}).get("transcription", "").lower()
    
    # Extract location mentions
    text_locations = text_result.get("entities", {}).get("location_mentions", [])
    
    # Common location keywords
    location_keywords = ["library", "cafeteria", "gym", "parking", "classroom", "lab", "pool", "office"]
    
    voice_locations = [loc for loc in location_keywords if loc in voice_transcription]
    
    if text_locations and voice_locations:
        # Check if they match
        text_locs_lower = [loc.lower() for loc in text_locations]
        mismatch = not any(vloc in text_locs_lower for vloc in voice_locations)
        
        if mismatch:
            return {
                "has_mismatch": True,
                "severity": "medium",
                "explanation": (
                    f"Location inconsistency: Text mentions '{', '.join(text_locations)}' "
                    f"but voice says '{', '.join(voice_locations)}'. "
                    f"Locations should match across all descriptions."
                ),
                "suggestions": [
                    "Ensure text and voice describe the same location",
                    "Re-record voice description with correct location",
                    "Update text to match voice"
                ]
            }
    
    return {"has_mismatch": False}


def check_condition_mismatch(
    image_result: Optional[Dict],
    text_result: Optional[Dict]
) -> Dict[str, Any]:
    """
    Detect condition descriptors (new/old/damaged) consistency.
    """
    if not image_result or not text_result:
        return {"has_mismatch": False}
    
    text = text_result.get("text", "")
    text_condition = _extract_condition(text)
    
    if not text_condition:
        return {"has_mismatch": False}
    
    # Analyze image quality as proxy for condition
    image_score = image_result.get("overall_score", 1.0)
    sharp_score = image_result.get("sharpness", {}).get("score", 100)
    
    # Simple heuristic: low quality might indicate damaged/used item
    if text_condition == "new" and (image_score < 0.6 or sharp_score < 80):
        return {
            "has_mismatch": True,
            "severity": "medium",
            "explanation": (
                "Condition mismatch: Description says 'new' but image quality suggests "
                "item may be used or damaged. Clear photos of new items typically have higher quality."
            ),
            "suggestions": [
                "Take a clearer photo in good lighting",
                "Verify item condition is actually 'new'",
                "Update description if item is used/damaged"
            ]
        }
    
    return {"has_mismatch": False}


# Export functions for use in enhanced XAIExplainer
__all__ = [
    "check_brand_mismatch",
    "check_location_consistency", 
    "check_condition_mismatch",
    "_extract_brands",
    "_extract_condition"
]
