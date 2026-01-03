import logging
from typing import Dict, List, Optional, Any, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EnhancedDiscrepancies')

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

def check_brand_mismatch(image_result: Dict, text_result: Dict) -> Dict[str, Any]:
    """
    Check if brands mentioned in text match brands visible in image (via OCR/Labels).
    
    NOTE: Currently limited - OCR is not always available, so we can only verify
    brands if OCR text is provided. We should NOT claim "brand not visible" 
    unless we've actually looked for it.
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
    
    if not has_ocr:
        # No OCR available - we cannot verify brand visibility
        # Don't make false claims about visibility
        logger.debug(f"Brand mentioned ({claimed_brands}) but no OCR available to verify")
        return {
            "has_mismatch": False,
            "note": f"Brand(s) mentioned: {', '.join(claimed_brands)} (visibility not verified - no OCR)"
        }
    
    # 3. Check if claimed brand is in OCR or Object Labels
    mismatches = []
    for brand in claimed_brands:
        # Check OCR
        brand_in_ocr = brand in ocr_text
        
        # Check Object Labels (e.g. if object detection returns 'apple_logo')
        objs_str = " ".join([f"{obj.get('class', '')} {obj.get('label', '')}".lower() for obj in image_objects])
        brand_in_objects = brand in objs_str

        if not brand_in_ocr and not brand_in_objects:
            mismatches.append(f"Text mentions '{brand}' but OCR didn't detect it in the image.")
            
    if mismatches:
        return {
            "has_mismatch": True,
            "explanation": "Brand visibility check: " + " ".join(mismatches),
            "severity": "low"  # Changed from medium to low since OCR isn't perfect
        }
        
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

def check_color_mismatch(image_result: Dict, text_result: Dict) -> Dict[str, Any]:
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
    
    # Get CLIP mismatch detection results if available
    mismatch_detection = image_result.get("mismatch_detection", {})
    attribute_scores = mismatch_detection.get("attribute_scores", {})
    predicted_colors = attribute_scores.get("predicted_colors", [])
    
    # Get mentioned colors from CLIP analysis
    clip_mentioned_colors = attribute_scores.get("mentioned_colors", [])
    
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
    
    # Also check using CLIP's mentioned_colors detection
    clip_mismatches = mismatch_detection.get("mismatches", [])
    for mm in clip_mismatches:
        if mm.get("type") == "color":
            mismatches.append("Color mentioned in text not prominent in image.")
            break
    
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
