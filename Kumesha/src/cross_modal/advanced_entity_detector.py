"""
Advanced Entity Detection Module
================================

Research-grade entity detection using CLIP zero-shot classification and EasyOCR.

Features:
1. Logo/Brand Detection - CLIP prompts for brand logos
2. Material Detection - CLIP prompts for textures
3. Size Estimation - CLIP categories for relative size
4. OCR Text Extraction - EasyOCR for serial numbers and text
5. Custom Entity Framework - Extensible detection system

Author: Multimodal Validation System
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import re

logger = logging.getLogger("AdvancedEntityDetector")

# ============================================================================
# CONSTANTS
# ============================================================================

KNOWN_BRANDS = [
    "apple", "samsung", "dell", "hp", "lenovo", "asus", "acer", "microsoft",
    "sony", "lg", "canon", "nikon", "nike", "adidas", "puma", "gucci",
    "louis vuitton", "prada", "rolex", "casio", "seiko", "bose", "jbl",
    "logitech", "razer", "corsair", "intel", "amd", "nvidia"
]

MATERIALS = [
    "leather", "metal", "plastic", "fabric", "wood", "glass", 
    "rubber", "ceramic", "cotton", "nylon", "canvas", "denim",
    "aluminum", "steel", "copper", "gold", "silver"
]

SIZE_CATEGORIES = [
    ("pocket-sized", "a very small pocket-sized object"),
    ("handheld", "a small handheld object"),
    ("small", "a small object"),
    ("medium", "a medium-sized object"),
    ("large", "a large object"),
    ("bulky", "a bulky large object")
]

# Lazy load heavy dependencies
_clip_model = None
_clip_preprocess = None
_easyocr_reader = None


# ============================================================================
# CLIP UTILITIES
# ============================================================================

def _get_clip():
    """Lazy load CLIP model."""
    global _clip_model, _clip_preprocess
    if _clip_model is None:
        try:
            import clip
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _clip_model, _clip_preprocess = clip.load("ViT-B/32", device=device)
            logger.info(f"✓ CLIP model loaded on {device}")
        except Exception as e:
            logger.error(f"Failed to load CLIP: {e}")
            raise
    return _clip_model, _clip_preprocess


def clip_score_prompts(image_path: str, prompts: List[str]) -> List[Tuple[str, float]]:
    """
    Score multiple prompts against an image using CLIP.
    
    Returns list of (prompt, score) tuples sorted by score descending.
    """
    try:
        import torch
        import clip
        from PIL import Image
        
        model, preprocess = _get_clip()
        device = next(model.parameters()).device
        
        # Load and preprocess image
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        
        # Tokenize prompts
        text_tokens = clip.tokenize(prompts).to(device)
        
        # Get embeddings
        with torch.no_grad():
            image_features = model.encode_image(image)
            text_features = model.encode_text(text_tokens)
            
            # Normalize
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity
            similarity = (image_features @ text_features.T).squeeze(0)
            scores = similarity.cpu().numpy().tolist()
        
        results = list(zip(prompts, scores))
        results.sort(key=lambda x: x[1], reverse=True)
        return results
        
    except Exception as e:
        logger.error(f"CLIP scoring failed: {e}")
        return []


# ============================================================================
# 1. LOGO/BRAND DETECTION
# ============================================================================

def detect_brand_logo(image_path: str, threshold: float = 0.25) -> Dict[str, Any]:
    """
    Detect brand logos in image using CLIP zero-shot classification.
    
    Args:
        image_path: Path to image file
        threshold: Minimum confidence threshold (0-1)
    
    Returns:
        Dict with detected brands and confidence scores
    """
    logger.info(f"[BRAND] Detecting brand logos in {image_path}")
    
    # Create prompts for each brand
    prompts = [f"a photo showing {brand} logo" for brand in KNOWN_BRANDS]
    
    try:
        results = clip_score_prompts(image_path, prompts)
        
        # Filter by threshold and map back to brand names
        detected = []
        for prompt, score in results:
            if score >= threshold:
                # Extract brand name from prompt
                brand = prompt.replace("a photo showing ", "").replace(" logo", "")
                detected.append({
                    "brand": brand,
                    "confidence": round(score, 3)
                })
        
        # Get top 3
        detected = detected[:3]
        
        logger.info(f"[BRAND] Detected: {[d['brand'] for d in detected]}")
        
        return {
            "detected_brands": detected,
            "top_brand": detected[0]["brand"] if detected else None,
            "top_confidence": detected[0]["confidence"] if detected else 0,
            "method": "CLIP-ZeroShot"
        }
        
    except Exception as e:
        logger.error(f"[BRAND] Detection failed: {e}")
        return {"detected_brands": [], "error": str(e)}


# ============================================================================
# 2. MATERIAL DETECTION
# ============================================================================

def detect_material(image_path: str, threshold: float = 0.25) -> Dict[str, Any]:
    """
    Detect material type (leather, metal, plastic, etc.) using CLIP.
    
    Args:
        image_path: Path to image file
        threshold: Minimum confidence threshold
    
    Returns:
        Dict with detected materials and confidence scores
    """
    logger.info(f"[MATERIAL] Detecting material in {image_path}")
    
    # Create prompts for materials
    prompts = [f"an object made of {m}" for m in MATERIALS]
    
    try:
        results = clip_score_prompts(image_path, prompts)
        
        detected = []
        for prompt, score in results:
            if score >= threshold:
                material = prompt.replace("an object made of ", "")
                detected.append({
                    "material": material,
                    "confidence": round(score, 3)
                })
        
        detected = detected[:3]
        
        logger.info(f"[MATERIAL] Detected: {[d['material'] for d in detected]}")
        
        return {
            "detected_materials": detected,
            "primary_material": detected[0]["material"] if detected else None,
            "primary_confidence": detected[0]["confidence"] if detected else 0,
            "method": "CLIP-ZeroShot"
        }
        
    except Exception as e:
        logger.error(f"[MATERIAL] Detection failed: {e}")
        return {"detected_materials": [], "error": str(e)}


# ============================================================================
# 3. SIZE ESTIMATION
# ============================================================================

def estimate_size(image_path: str) -> Dict[str, Any]:
    """
    Estimate relative size category of object in image.
    
    Note: This provides relative size estimation, not absolute dimensions.
    Absolute measurements would require depth sensors or reference objects.
    
    Returns:
        Dict with size category and confidence
    """
    logger.info(f"[SIZE] Estimating size for {image_path}")
    
    # Create prompts for size categories
    prompts = [desc for _, desc in SIZE_CATEGORIES]
    
    try:
        results = clip_score_prompts(image_path, prompts)
        
        # Map back to category names
        size_results = []
        for prompt, score in results:
            for cat_name, cat_desc in SIZE_CATEGORIES:
                if cat_desc == prompt:
                    size_results.append({
                        "category": cat_name,
                        "confidence": round(score, 3)
                    })
                    break
        
        primary = size_results[0] if size_results else None
        
        logger.info(f"[SIZE] Estimated: {primary['category'] if primary else 'unknown'}")
        
        return {
            "size_category": primary["category"] if primary else "unknown",
            "confidence": primary["confidence"] if primary else 0,
            "all_categories": size_results[:3],
            "method": "CLIP-ZeroShot",
            "note": "Relative size estimation only. Absolute dimensions require reference objects."
        }
        
    except Exception as e:
        logger.error(f"[SIZE] Estimation failed: {e}")
        return {"size_category": "unknown", "error": str(e)}


# ============================================================================
# 4. OCR TEXT EXTRACTION
# ============================================================================

def _get_ocr_reader():
    """Lazy load EasyOCR reader."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(['en'], gpu=True)
            logger.info("✓ EasyOCR reader loaded")
        except Exception as e:
            logger.warning(f"EasyOCR GPU failed, trying CPU: {e}")
            try:
                import easyocr
                _easyocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("✓ EasyOCR reader loaded (CPU)")
            except Exception as e2:
                logger.error(f"EasyOCR failed to load: {e2}")
                raise
    return _easyocr_reader


def extract_serial_patterns(texts: List[str]) -> List[str]:
    """
    Extract potential serial numbers from OCR text.
    
    Patterns matched:
    - Alphanumeric sequences 6+ chars (e.g., "ABC123DEF")
    - Model numbers (e.g., "A1234", "XPS-15")
    - Serial patterns (e.g., "SN:12345678")
    """
    serial_patterns = [
        r'[A-Z0-9]{6,}',  # Basic alphanumeric
        r'[A-Z]{1,3}[-]?\d{3,}',  # Model numbers like "XPS-15", "A1234"
        r'S/?N[:\s]?[A-Z0-9]+',  # Serial number prefix
        r'\d{2,}[-/]\d{2,}[-/]\d{2,}',  # Date-like patterns
    ]
    
    found = []
    for text in texts:
        text_upper = text.upper().strip()
        for pattern in serial_patterns:
            matches = re.findall(pattern, text_upper)
            found.extend(matches)
    
    # Remove duplicates and very short matches
    found = list(set([s for s in found if len(s) >= 4]))
    return found


def extract_text_ocr(image_path: str) -> Dict[str, Any]:
    """
    Extract all visible text from image using OCR.
    
    Returns:
        Dict containing:
        - texts: List of detected text strings
        - confidence_scores: Confidence for each text
        - serial_numbers: Potential serial numbers found
        - all_text: Combined text as single string
    """
    logger.info(f"[OCR] Extracting text from {image_path}")
    
    try:
        reader = _get_ocr_reader()
        results = reader.readtext(image_path)
        
        texts = [r[1] for r in results]
        confidences = [r[2] for r in results]
        
        # Extract serial numbers
        serials = extract_serial_patterns(texts)
        
        # Combine all text
        all_text = " ".join(texts)
        
        logger.info(f"[OCR] Found {len(texts)} text regions, {len(serials)} potential serials")
        
        return {
            "texts": texts,
            "confidence_scores": [round(c, 3) for c in confidences],
            "serial_numbers": serials,
            "all_text": all_text,
            "text_count": len(texts),
            "method": "EasyOCR"
        }
        
    except ImportError:
        logger.warning("[OCR] EasyOCR not installed. Run: pip install easyocr")
        return {
            "texts": [],
            "error": "EasyOCR not installed",
            "install_hint": "pip install easyocr"
        }
    except Exception as e:
        logger.error(f"[OCR] Extraction failed: {e}")
        return {"texts": [], "error": str(e)}


# ============================================================================
# 5. CUSTOM ENTITY FRAMEWORK
# ============================================================================

class CustomEntityDetector:
    """
    Extensible framework for detecting user-defined entities.
    
    Usage:
        detector = CustomEntityDetector()
        detector.register_entity("car_brand", 
            prompts=["a photo of a Toyota car", "a photo of a Honda car", ...],
            threshold=0.3
        )
        result = detector.detect(image_path, "car_brand")
    """
    
    def __init__(self):
        self.entities: Dict[str, Dict] = {}
        self._register_default_entities()
    
    def _register_default_entities(self):
        """Register some useful default custom entities."""
        
        # Condition/Quality
        self.register_entity("condition", [
            ("new", "a brand new item in perfect condition"),
            ("excellent", "an item in excellent condition"),
            ("good", "an item in good used condition"),
            ("fair", "an item in fair condition with visible wear"),
            ("poor", "an item in poor condition with damage"),
        ])
        
        # Device state
        self.register_entity("device_state", [
            ("powered_on", "an electronic device that is turned on"),
            ("powered_off", "an electronic device that is turned off"),
            ("charging", "a device that is charging"),
        ])
        
        # Package state
        self.register_entity("packaging", [
            ("sealed", "a sealed unopened package"),
            ("opened", "an opened package"),
            ("damaged_package", "a damaged package"),
        ])
    
    def register_entity(
        self, 
        name: str, 
        prompts: List[Tuple[str, str]], 
        threshold: float = 0.25
    ):
        """
        Register a custom entity for detection.
        
        Args:
            name: Entity type name (e.g., "car_brand")
            prompts: List of (label, description) tuples
            threshold: Minimum confidence threshold
        """
        self.entities[name] = {
            "prompts": prompts,
            "threshold": threshold
        }
        logger.info(f"[CUSTOM] Registered entity '{name}' with {len(prompts)} prompts")
    
    def list_entities(self) -> List[str]:
        """List all registered entity types."""
        return list(self.entities.keys())
    
    def detect(self, image_path: str, entity_name: str) -> Dict[str, Any]:
        """
        Detect custom entity in image.
        
        Args:
            image_path: Path to image
            entity_name: Registered entity type name
            
        Returns:
            Dict with detection results
        """
        if entity_name not in self.entities:
            return {
                "error": f"Unknown entity type: {entity_name}",
                "available": self.list_entities()
            }
        
        entity = self.entities[entity_name]
        prompts_list = [desc for _, desc in entity["prompts"]]
        labels = [label for label, _ in entity["prompts"]]
        
        try:
            results = clip_score_prompts(image_path, prompts_list)
            
            # Map scores to labels
            detected = []
            for prompt, score in results:
                for label, desc in entity["prompts"]:
                    if desc == prompt and score >= entity["threshold"]:
                        detected.append({
                            "label": label,
                            "confidence": round(score, 3)
                        })
                        break
            
            return {
                "entity_type": entity_name,
                "detected": detected[:3],
                "top_match": detected[0]["label"] if detected else None,
                "top_confidence": detected[0]["confidence"] if detected else 0,
                "method": "CLIP-ZeroShot-Custom"
            }
            
        except Exception as e:
            logger.error(f"[CUSTOM] Detection failed for {entity_name}: {e}")
            return {"error": str(e)}


# Singleton instance
_custom_detector = None

def get_custom_entity_detector() -> CustomEntityDetector:
    """Get or create singleton CustomEntityDetector instance."""
    global _custom_detector
    if _custom_detector is None:
        _custom_detector = CustomEntityDetector()
    return _custom_detector


# ============================================================================
# UNIFIED DETECTION FUNCTION
# ============================================================================

def detect_all_entities(image_path: str, text_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Run all entity detection on an image.
    
    Args:
        image_path: Path to image
        text_hint: Optional text description for context
    
    Returns:
        Dict with all detection results
    """
    logger.info(f"[ALL] Running comprehensive entity detection on {image_path}")
    
    results = {
        "image_path": image_path,
        "text_hint": text_hint,
    }
    
    # 1. Brand detection
    try:
        results["brand"] = detect_brand_logo(image_path)
    except Exception as e:
        results["brand"] = {"error": str(e)}
    
    # 2. Material detection
    try:
        results["material"] = detect_material(image_path)
    except Exception as e:
        results["material"] = {"error": str(e)}
    
    # 3. Size estimation
    try:
        results["size"] = estimate_size(image_path)
    except Exception as e:
        results["size"] = {"error": str(e)}
    
    # 4. OCR
    try:
        results["ocr"] = extract_text_ocr(image_path)
    except Exception as e:
        results["ocr"] = {"error": str(e)}
    
    # 5. Custom entities (condition)
    try:
        detector = get_custom_entity_detector()
        results["condition"] = detector.detect(image_path, "condition")
    except Exception as e:
        results["condition"] = {"error": str(e)}
    
    logger.info(f"[ALL] Detection complete")
    return results


# ============================================================================
# TEST / DEMO
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python advanced_entity_detector.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"\nTesting advanced entity detection on: {image_path}\n")
    
    results = detect_all_entities(image_path)
    
    import json
    print(json.dumps(results, indent=2))
