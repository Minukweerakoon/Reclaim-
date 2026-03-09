import logging
from typing import Dict, List, Optional, Any, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EnhancedDiscrepancies')

def _convert_to_py_type(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    import numpy as np
    if isinstance(obj, (np.bool_, np.bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _convert_to_py_type(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_py_type(i) for i in obj]
    return obj


def _extract_brands(text: str) -> List[str]:
    """
    Extract potential brand names from text using basic heuristics.
    In a real system, this would use a NER model or Brand Knowledge Graph.
    """
    # Common tech/clothing brands for demo
    known_brands = {
        "apple", "samsung", "sony", "nike", "adidas", "gucci", "dell", "hp", 
        "lenovo", "asus", "canon", "nikon", "rolex", "casio", "microsoft", "lg"
    }
    
    found_brands = []
    words = text.lower().replace(',', '').replace('.', '').split()
    for word in words:
        if word in known_brands:
            found_brands.append(word)
            
    return found_brands

def _extract_condition(text: str) -> Optional[str]:
    """Extract condition claims from text."""
    text_lower = text.lower()
    if any(x in text_lower for x in ["brand new", "mint condition", "unused"]):
        return "new"
    if any(x in text_lower for x in ["used", "old", "worn", "scratched", "broken"]):
        return "used"
    if any(x in text_lower for x in ["good condition", "excellent condition"]):
        return "good"
    return None

def check_brand_mismatch(image_result: Dict, text_result: Dict, image_path: str = None) -> Dict[str, Any]:
    """
    Check if brands mentioned in text match brands visible in image.
    Uses OCR first, then falls back to CLIP zero-shot brand detection.
    """
    text = text_result.get("text", "")
    ocr_text = image_result.get("ocr_text", "").lower()
    image_objects = image_result.get("objects", {}).get("detections", [])
    
    # 1. Extract brands from user text
    claimed_brands = _extract_brands(text)
    if not claimed_brands:
        return {"has_mismatch": False}
    
    # 2. Check if we have OCR data to verify brands
    has_ocr = bool(ocr_text.strip())
    
    mismatches = []
    detected_brand = None
    
    if has_ocr:
        # 3a. Check if claimed brand is in OCR or Object Labels
        for brand in claimed_brands:
            brand_in_ocr = brand in ocr_text
            objs_str = " ".join([f"{obj.get('class', '')} {obj.get('label', '')}".lower() for obj in image_objects])
            brand_in_objects = brand in objs_str
            
            if not brand_in_ocr and not brand_in_objects:
                mismatches.append(f"Text mentions '{brand}' but OCR didn't detect it in the image.")
    else:
        # 3b. No OCR - use CLIP zero-shot brand detection
        if image_path:
            try:
                from src.cross_modal.advanced_entity_detector import detect_brand_logo
                brand_result = detect_brand_logo(image_path, threshold=0.20)  # Lowered from 0.25
                detected_brand = brand_result.get("top_brand")
                detected_confidence = brand_result.get("top_confidence", 0)
                
                if detected_brand and detected_confidence >= 0.20:  # Lowered from 0.25
                    # Check if detected brand conflicts with claimed brand
                    for claimed in claimed_brands:
                        if claimed.lower() != detected_brand.lower():
                            mismatches.append(
                                f"Brand mismatch: Text says '{claimed}' but image shows '{detected_brand}' logo (confidence: {detected_confidence:.0%})."
                            )
                            break
            except Exception as e:
                logger.warning(f"CLIP brand detection failed: {e}")
                # Fall through - no mismatch detected if we can't verify
    
    if mismatches:
        result = {
            "has_mismatch": True,
            "explanation": " ".join(mismatches),
            "severity": "high" if detected_brand else "low",
            "details": {
                "claimed_brands": claimed_brands,
                "detected_brand": detected_brand,
                "source": "CLIP-ZeroShot" if detected_brand else "OCR"
            }
        }
        return _convert_to_py_type(result)
        
    return {"has_mismatch": False}

def check_location_consistency(text_result: Dict, voice_result: Dict) -> Dict[str, Any]:
    """
    Check if location in text matches location in voice.
    """
    if not voice_result:
        return {"has_mismatch": False}
        
    text_locs = text_result.get("entities", {}).get("location_mentions", [])
    if not text_locs:
        # Try finding known locations in text if entities extraction failed/not present
        known_places = ["library", "canteen", "cafeteria", "gym", "lab", "office", "park", "bus stop"]
        text_lower = text_result.get("text", "").lower()
        text_locs = [p for p in known_places if p in text_lower]

    voice_transcription = voice_result.get("transcription", {}).get("transcription", "").lower()
    
    if not text_locs:
        return {"has_mismatch": False}
        
    mismatches = []
    
    # Identify voice locations
    distinct_places = ["library", "canteen", "cafeteria", "gym", "lab", "office", "park", "bus stop"]
    voice_places = [p for p in distinct_places if p in voice_transcription]
    
    for loc in text_locs:
        loc_lower = loc.lower()
        for v_loc in voice_places:
            # Conflict if different place names
            if v_loc != loc_lower and v_loc not in loc_lower and loc_lower not in v_loc:
                 mismatches.append(f"Text says '{loc}' but voice mentions '{v_loc}'")
    
    if mismatches:
        return {
            "has_mismatch": True,
            "explanation": "Location inconsistency detected: " + "; ".join(mismatches),
            "severity": "high"
        }
    
    return {"has_mismatch": False}

def check_color_mismatch(image_result: Dict, text_result: Dict, cross_modal_result: Dict = None) -> Dict[str, Any]:
    """
    Check if colors mentioned in text match colors detected in the image.
    Uses CLIP mismatch detection and dominant color analysis.
    """
    text = text_result.get("text", "")
    
    # Common color keywords to check for
    color_keywords = [
        "red", "blue", "green", "yellow", "black", "white", "brown",
        "gray", "grey", "orange", "purple", "pink", "silver", "gold"
    ]
    
    # Extract colors mentioned in text
    text_lower = text.lower()
    mentioned_colors = [color for color in color_keywords if color in text_lower]
    
    if not mentioned_colors:
        return {"has_mismatch": False}
    
    # FIRST: Check CLIP cross-modal feedback (most reliable)
    if cross_modal_result:
        clip_result = cross_modal_result.get("image_text", {})
        clip_feedback = clip_result.get("feedback", "")
        clip_mismatch_detection = clip_result.get("mismatch_detection", {})
        
        # Check if CLIP feedback mentions color mismatch (relaxed condition)
        if "appears" in clip_feedback or "mismatch" in clip_feedback:
            # Extract what CLIP detected
            import re
            # Pattern: "Text mentions 'X' but image appears 'Y'"
            match = re.search(r"mentions ['\"]?(\w+)['\"]? but.*appears ['\"]?(\w+)['\"]?", clip_feedback, re.IGNORECASE)
            if match:
                mentioned_color = match.group(1).lower()
                detected_color = match.group(2).lower()
                
                # Verify at least one of them is a color to be safe
                if mentioned_color in color_keywords or detected_color in color_keywords:
                    result = {
                        "has_mismatch": True,
                        "explanation": f"Color mismatch: Text says '{mentioned_color}' but image shows '{detected_color}'.",
                        "severity": "high",
                        "details": {
                            "mentioned_colors": [mentioned_color],
                            "detected_color": detected_color,
                            "source": "CLIP cross-modal analysis"
                        }
                    }
                    return _convert_to_py_type(result)
        
        # Check mismatch_detection structure
        clip_mismatches = clip_mismatch_detection.get("mismatches", [])
        for mm in clip_mismatches:
            if mm.get("type") == "color":
                return {
                    "has_mismatch": True,
                    "explanation": f"Color mismatch detected: {mm.get('description', 'Colors do not match')}",
                    "severity": "medium"
                }
    
    # SECOND: Fallback to image_result mismatch detection
    mismatch_detection = image_result.get("mismatch_detection", {})
    attribute_scores = mismatch_detection.get("attribute_scores", {})
    predicted_colors = attribute_scores.get("predicted_colors", [])
    
    # Check for color conflicts
    mismatches = []
    
    if predicted_colors and mentioned_colors:
        # Extract top predicted color from CLIP
        if len(predicted_colors) > 0:
            top_color_info = predicted_colors[0]
            if isinstance(top_color_info, tuple) and len(top_color_info) >= 1:
                # Format is like ("black color", score)
                top_color_str = top_color_info[0]
                # Extract color name ("black color" -> "black")
                top_color = top_color_str.split()[0] if " " in top_color_str else top_color_str
                
                # Check if any mentioned color matches the top predicted color
                if not any(mc in top_color for mc in mentioned_colors):
                    mismatches.append(
                        f"Text mentions '{', '.join(mentioned_colors)}' but image appears to be '{top_color}'."
                    )
    
    if mismatches:
        return {
            "has_mismatch": True,
            "explanation": "Color mismatch detected: " + " ".join(mismatches),
            "severity": "medium",
            "details": {
                "mentioned_colors": mentioned_colors,
                "predicted_colors": [p[0] if isinstance(p, tuple) else str(p) for p in predicted_colors[:3]] if predicted_colors else []
            }
        }
    
    return {"has_mismatch": False}

def check_condition_mismatch(image_result: Dict, text_result: Dict) -> Dict[str, Any]:
    """
    Check consistency between "New/Used" text claims and Image Quality/Sharpness.
    """
    text = text_result.get("text", "")
    condition_claim = _extract_condition(text)
    
    if not condition_claim:
        return {"has_mismatch": False}
        
    # Image metrics
    sharpness_score = image_result.get("sharpness", {}).get("score", 0)
    overall_quality = image_result.get("overall_score", 0)
    
    mismatches = []
    
    if condition_claim == "new":
        # Heuristic: Claiming "new" but having very poor image quality/blur is suspicious
        # Or if we had a "scratch detection" model, we'd check that.
        # For now, rely on overall quality score.
        if overall_quality < 0.6: 
             mismatches.append(f"Item described as '{condition_claim}' but image quality is low ({overall_quality:.2f}).")
             
    if mismatches:
        return {
            "has_mismatch": True, 
            "explanation": " ".join(mismatches),
            "severity": "medium"
        }
        
    return {"has_mismatch": False}
