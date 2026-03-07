import os
import time
import logging
import json
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
import torch
from sentence_transformers import SentenceTransformer
from datetime import datetime
from src.cross_modal.clip_validator import CLIPValidator
# Import new Cross-Attention Fusion
try:
    from src.cross_modal.fusion import CrossAttentionFusion
except ImportError:
    CrossAttentionFusion = None

# Import XAI Explainer
try:
    from src.cross_modal.xai_explainer import XAIExplainer
except ImportError as e:
    logging.warning(f"Failed to import XAIExplainer: {e}")
    XAIExplainer = None

# Import Confidence Calibrator (Research Enhancement)
try:
    from src.intelligence.confidence_calibration import ConfidenceCalibrator
except ImportError as e:
    logging.warning(f"Failed to import ConfidenceCalibrator: {e}")
    ConfidenceCalibrator = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ConsistencyEngine')

class ConsistencyEngine:
    """An advanced multi-modal consistency validation system integrating text, audio, and image inputs."""
    
    def __init__(self, enable_logging: bool = True):
        """Initialize the ConsistencyEngine."""
        self.enable_logging = enable_logging
        self.clip_validator = CLIPValidator()
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_similarity_threshold = 0.75

        # Initialize Cross-Attention Fusion (Heuristic Mode)
        self.fusion_model = None
        if CrossAttentionFusion:
            try:
                self.fusion_model = CrossAttentionFusion()
                self.fusion_model.eval()
                logger.info("Cross-Attention Fusion model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Fusion model: {e}")
                self.fusion_model = None
        else:
            logger.warning("CrossAttentionFusion not available (import failed)")

        # Initialize XAI Explainer
        self.xai_explainer = None
        if XAIExplainer:
            try:
                self.xai_explainer = XAIExplainer()
                logger.info("XAI Explainer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize XAI Explainer: {e}")
                self.xai_explainer = None
        else:
            logger.warning("XAI Explainer not available (import failed)")

        # Initialize Confidence Calibrator (Research Enhancement)
        self.confidence_calibrator = None
        self._calibrator_fitted = False
        if ConfidenceCalibrator:
            try:
                self.confidence_calibrator = ConfidenceCalibrator(method="isotonic")
                logger.info("Confidence Calibrator initialized (unfitted)")
            except Exception as e:
                logger.warning(f"Failed to initialize Confidence Calibrator: {e}")
                self.confidence_calibrator = None
        else:
            logger.warning("Confidence Calibrator not available (import failed)")


        self.location_keywords = [
            "library",
            "cafeteria",
            "classroom",
            "lab",
            "gym",
            "parking",
            "auditorium",
            "office",
            "hallway",
            "restroom",
            "entrance",
            "exit",
            "bus stop",
            "hostel",
        ]
        self.temporal_keywords = [
            "morning",
            "afternoon",
            "evening",
            "night",
            "noon",
            "midnight",
            "today",
            "yesterday",
            "last night",
            "last week",
            "weekend",
            "8 am",
            "9 am",
            "10 am",
            "11 am",
            "12 pm",
            "1 pm",
            "2 pm",
            "3 pm",
            "4 pm",
        ]
    
    # ------------------------------------------------------------------ #
    # Adaptive Thresholds by Item Category
    # ------------------------------------------------------------------ #
    # Electronics (phones, laptops) need higher image quality because
    # model numbers and distinguishing features are harder to see in poor images.
    # Clothing/accessories can be validated with lower thresholds.
    CATEGORY_THRESHOLDS = {
        "electronics": {
            "image_quality": 0.80,
            "text_completeness": 0.75,
            "clip_similarity": 0.70,
            "voice_quality": 0.70,
            "description": "High-value electronics require clear images for model identification"
        },
        "phone": {
            "image_quality": 0.80,
            "text_completeness": 0.75,
            "clip_similarity": 0.70,
            "voice_quality": 0.70,
            "description": "Phones have many similar models, need detailed identification"
        },
        "laptop": {
            "image_quality": 0.75,
            "text_completeness": 0.70,
            "clip_similarity": 0.65,
            "voice_quality": 0.65,
            "description": "Laptops are larger but still need brand/model clarity"
        },
        "accessories": {
            "image_quality": 0.65,
            "text_completeness": 0.60,
            "clip_similarity": 0.55,
            "voice_quality": 0.55,
            "description": "Accessories like keys/glasses are more visually distinct"
        },
        "bag": {
            "image_quality": 0.65,
            "text_completeness": 0.65,
            "clip_similarity": 0.60,
            "voice_quality": 0.55,
            "description": "Bags have distinctive colors and styles"
        },
        "wallet": {
            "image_quality": 0.70,
            "text_completeness": 0.70,
            "clip_similarity": 0.65,
            "voice_quality": 0.60,
            "description": "Wallets often contain ID, moderate quality needed"
        },
        "jewelry": {
            "image_quality": 0.85,
            "text_completeness": 0.80,
            "clip_similarity": 0.75,
            "voice_quality": 0.70,
            "description": "Jewelry is high-value and needs detailed verification"
        },
        "clothing": {
            "image_quality": 0.55,
            "text_completeness": 0.55,
            "clip_similarity": 0.50,
            "voice_quality": 0.50,
            "description": "Clothing is visually distinctive, lower thresholds acceptable"
        },
        "documents": {
            "image_quality": 0.80,
            "text_completeness": 0.85,
            "clip_similarity": 0.60,
            "voice_quality": 0.65,
            "description": "Documents need high text completeness for identification"
        },
        "default": {
            "image_quality": 0.70,
            "text_completeness": 0.70,
            "clip_similarity": 0.65,
            "voice_quality": 0.60,
            "description": "Standard thresholds for unspecified items"
        }
    }
        
    def validate_voice_text_consistency(self, 
                                       voice_transcription: str, 
                                       text_description: str) -> Dict:
        """
        Validate consistency between voice and text using sentence embeddings.
        
        Returns:
        {
            "valid": bool,
            "similarity": float,
            "threshold": float,
            "feedback": str
        }
        """
        result = {
            "valid": False,
            "similarity": 0.0,
            "threshold": self.text_similarity_threshold,
            "feedback": ""
        }
        
        try:
            # Encode both texts
            embeddings = self.sentence_model.encode([voice_transcription, text_description])
            # Calculate cosine similarity
            similarity = float(np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])))
            result["similarity"] = similarity
            
            # Determine validity based on threshold
            result["valid"] = bool(similarity >= self.text_similarity_threshold)
            
            if result["valid"]:
                result["feedback"] = "Voice and text are semantically consistent"
            else:
                result["feedback"] = f"Voice and text are not well aligned (similarity: {similarity:.2f}, threshold: {self.text_similarity_threshold})"
            
        except Exception as e:
            if getattr(self, 'enable_logging', False):
                logger.error(f"Error during voice-text consistency validation: {str(e)}")
            result["feedback"] = f"Error during voice-text consistency validation: {str(e)}"
        
        return result
    
    def validate_multimodal_fusion(self, 
                                 text_embedding: np.ndarray,
                                 image_embedding: np.ndarray,
                                 voice_embedding: Optional[np.ndarray] = None) -> Dict:
        """
        Validate consistency using Cross-Attention Fusion.
        This provides a superior, learnable metric compared to simple cosine similarity.
        """
        result = {
            "valid": False,
            "score": 0.0,
            "method": "heuristic",
            "feedback": ""
        }
        
        if not self.fusion_model:
            result["feedback"] = "Fusion model not initialized"
            return result
            
        try:
            # Normalize embeddings (important for attention/cosine)
            def normalize(v):
                n = np.linalg.norm(v)
                return v / n if n > 0 else v
                
            text_norm = normalize(text_embedding)
            image_norm = normalize(image_embedding)
            voice_norm = normalize(voice_embedding) if voice_embedding is not None else None
            
            # Use heuristic fusion (since we haven't trained the weights yet)
            # In a trained model, we would use self.fusion_model(t, i, v)
            score = self.fusion_model.fuse_features_heuristic(
                text_norm, image_norm, voice_norm
            )
            
            result["score"] = float(score)
            result["valid"] = score >= 0.65  # Threshold
            result["method"] = "cross_attention_heuristic"
            
            if result["valid"]:
                result["feedback"] = "High cross-modal alignment detected"
            else:
                result["feedback"] = f"Low cross-modal alignment ({score:.2f})"
                
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error in multimodal fusion: {e}")
            result["feedback"] = f"Fusion error: {str(e)}"
            
        return result

    def validate_context_consistency(
        self,
        text_result: Optional[Dict[str, Any]],
        voice_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate location and temporal alignment between modalities."""
        result = {
            "valid": True,
            "score": 1.0,
            "location_match": True,
            "temporal_match": True,
            "text_locations": [],
            "voice_locations": [],
            "text_temporal": [],
            "voice_temporal": [],
            "feedback": "",
        }

        if not text_result or not voice_result:
            result["feedback"] = "Insufficient data for context comparison"
            return result

        text_body = text_result.get("text", "") or ""
        voice_transcription = (
            voice_result.get("transcription", {}).get("transcription", "") or ""
        )

        def detect_keywords(text: str, keywords: List[str]) -> List[str]:
            lowered = text.lower()
            hits = []
            for kw in keywords:
                if kw in lowered:
                    hits.append(kw)
            seen = []
            for kw in hits:
                if kw not in seen:
                    seen.append(kw)
            return seen

        voice_locations = detect_keywords(voice_transcription, self.location_keywords)
        text_locations = []
        entities = (text_result or {}).get("entities", {})
        if isinstance(entities, dict):
            text_locations = entities.get("location_mentions", []) or []
        if not text_locations:
            text_locations = detect_keywords(text_body, self.location_keywords)

        voice_temporal = detect_keywords(voice_transcription, self.temporal_keywords)
        text_temporal = detect_keywords(text_body, self.temporal_keywords)

        result["text_locations"] = text_locations
        result["voice_locations"] = voice_locations
        result["text_temporal"] = text_temporal
        result["voice_temporal"] = voice_temporal

        def score_component(text_terms: List[str], voice_terms: List[str]) -> float:
            if not text_terms and not voice_terms:
                return 0.8
            if text_terms and voice_terms:
                return 1.0 if set(text_terms) & set(voice_terms) else 0.3
            if text_terms:
                return 0.5
            return 0.6

        location_score = score_component(text_locations, voice_locations)
        temporal_score = score_component(text_temporal, voice_temporal)

        result["location_match"] = location_score >= 0.7
        result["temporal_match"] = temporal_score >= 0.7
        overall = (location_score + temporal_score) / 2
        result["score"] = round(overall, 2)
        result["valid"] = result["score"] >= 0.7

        if result["valid"]:
            result["feedback"] = "Context information is consistent across modalities"
        else:
            messages = []
            if not result["location_match"]:
                messages.append("Locations differ between text and voice.")
            if not result["temporal_match"]:
                messages.append("Temporal references differ between text and voice.")
            result["feedback"] = " ".join(messages) or "Context mismatch detected."

        return result



    

    

    

    

    

    
    def calculate_overall_confidence(self, 
                                    image_result: dict, 
                                    text_result: dict,
                                    voice_result: dict, 
                                    cross_modal_results: dict) -> Dict:
        """
        Calculate comprehensive confidence score.
        
        Weighting:
        - Image score: 25%
        - Text score: 25%
        - Voice score: 20%
        - CLIP similarity: 20%
        - Voice-text similarity: 10%
        
        Routing Logic:
        - High quality (≥0.85): Forward to matching engine
        - Medium quality (0.70-0.84): Manual review queue
        - Low quality (<0.70): Return for improvement
        
        Returns:
        {
            "overall_confidence": float,
            "routing": str,  # "high_quality", "medium_quality", "low_quality"
            "action": str,  # "forward_to_matching", "manual_review", "return_for_improvement"
            "individual_scores": dict,
            "cross_modal_scores": dict
        }
        """
        overall_confidence = 0.0
        individual_scores = {}
        cross_modal_scores = {}
        
        def _normalize_score(value: float) -> float:
            if value is None:
                return 0.0
            return value / 100.0 if value > 1.0 else value

        # Collect individual scores — always use the score value even if
        # the modality didn't pass its own quality threshold ("valid" flag).
        # Gating behind "valid" would zero-out a 65% image score just because
        # it's below the 70% quality threshold, causing the Confidence Core
        # to show "—" when there IS useful data.
        if image_result:
            individual_scores["image"] = _normalize_score(image_result.get("overall_score", 0.0))
        else:
            individual_scores["image"] = 0.0

        if text_result:
            individual_scores["text"] = _normalize_score(text_result.get("overall_score", 0.0))
        else:
            individual_scores["text"] = 0.0

        if voice_result:
            individual_scores["voice"] = _normalize_score(voice_result.get("overall_score", voice_result.get("confidence", 0.0)))
        else:
            individual_scores["voice"] = 0.0

        # Collect cross-modal scores
        if cross_modal_results:
            if "image_text" in cross_modal_results:
                cross_modal_scores["clip_similarity"] = cross_modal_results["image_text"].get("similarity", 0.0)
            if "voice_text" in cross_modal_results:
                cross_modal_scores["voice_text_similarity"] = cross_modal_results["voice_text"].get("similarity", 0.0)
            if "context" in cross_modal_results:
                cross_modal_scores["context_consistency"] = cross_modal_results["context"].get("score", 0.0)

        # Adaptive Weighting Logic
        # 1. Identify present modalities
        present_modalities = []
        if individual_scores["image"] > 0: present_modalities.append("image")
        if individual_scores["text"] > 0: present_modalities.append("text")
        if individual_scores["voice"] > 0: present_modalities.append("voice")
        
        # 2. Redistribute weights dynamically
        # Base weights
        active_weights = {
            "image": 0.25,
            "text": 0.25,
            "voice": 0.20,
            "clip": 0.20,
            "voice_text": 0.10
        }
        
        if len(present_modalities) == 1:
            # If only one modality is present, assign it 100% weight
            active_weights = {k: 0.0 for k in active_weights}
            active_weights[present_modalities[0]] = 1.0
        else:
            # Adjust based on missing inputs
            if "voice" not in present_modalities:
                # Distribute voice-related weights (0.20 + 0.10 = 0.30) to image and text
                # New split: Image (0.45), Text (0.40), CLIP (0.15)
                active_weights = {
                    "image": 0.45,
                    "text": 0.40,
                    "voice": 0.0,
                    "clip": 0.15,
                    "voice_text": 0.0
                }
            
            if "image" not in present_modalities:
                 # Distribute image-related weights (0.25 + 0.20 = 0.45)
                 # AGGRESSIVE: Boost text to 70% when image is completely missing
                 # New split: Text (0.70), Voice (0.20), Voice-Text (0.10)
                 active_weights = {
                    "image": 0.0,
                    "text": 0.70,  # Increased from 0.60 to 70%
                    "voice": 0.20,
                    "clip": 0.0,
                    "voice_text": 0.10
                 }

        # Calculate overall confidence with adaptive weights
        overall_confidence += individual_scores["image"] * active_weights["image"]
        overall_confidence += individual_scores["text"] * active_weights["text"]
        overall_confidence += individual_scores["voice"] * active_weights["voice"]
        overall_confidence += cross_modal_scores.get("clip_similarity", 0.0) * active_weights["clip"]
        
        # IMPROVEMENT: If both image and text are present, add strong agreement bonus
        if individual_scores["image"] > 0.45 and individual_scores["text"] > 0.55:
            # Both modalities strong, add positive bonus
            agreement_bonus = 0.10 * (individual_scores["image"] + individual_scores["text"]) / 2  # Increased to 10%
            overall_confidence = min(0.99, overall_confidence + agreement_bonus)
            logger.info(f"✓ Image-Text Agreement Bonus: +{agreement_bonus:.1%}")
        
        voice_text_component = cross_modal_scores.get("voice_text_similarity", 0.0)
        if "context_consistency" in cross_modal_scores:
            context_score = cross_modal_scores["context_consistency"]
            voice_text_component = 0.7 * voice_text_component + 0.3 * context_score
            
        overall_confidence += voice_text_component * active_weights["voice_text"]

        # Apply contradiction penalties so high per-modality quality does not hide
        # explicit cross-modal mismatches (item/color/brand conflicts).
        penalties = {
            "mismatch_penalty": 0.0,
            "applied_reasons": []
        }
        image_text = (cross_modal_results or {}).get("image_text", {}) or {}
        mismatch_types = [
            str(mm.get("type", "")).lower()
            for mm in image_text.get("mismatch_detection", {}).get("mismatches", [])
            if isinstance(mm, dict)
        ]

        penalty_by_type = {
            "item": 0.20,
            "brand": 0.16,
            "color": 0.10,
        }
        for mismatch_type in mismatch_types:
            penalties["mismatch_penalty"] += penalty_by_type.get(mismatch_type, 0.08)
            penalties["applied_reasons"].append(f"mismatch:{mismatch_type}")

        if image_text and not image_text.get("valid", True) and penalties["mismatch_penalty"] < 0.10:
            penalties["mismatch_penalty"] = 0.10
            penalties["applied_reasons"].append("image_text_invalid")

        penalties["mismatch_penalty"] = min(0.35, penalties["mismatch_penalty"])
        overall_confidence -= penalties["mismatch_penalty"]

        overall_confidence = max(0.0, min(1.0, overall_confidence))

        # Apply calibration if available (Research Enhancement)
        calibrated_confidence = overall_confidence
        calibration_applied = False
        if self.confidence_calibrator and self._calibrator_fitted:
            try:
                calibrated_confidence = self.confidence_calibrator.calibrate(overall_confidence)
                calibration_applied = True
            except Exception as e:
                logger.warning(f"Calibration failed, using raw confidence: {e}")

        rounded_confidence = round(calibrated_confidence, 2)

        # Determine routing and action based on calibrated confidence
        routing = "low_quality"
        action = "return_for_improvement"
        if rounded_confidence >= 0.65:  # FINAL PUSH: 0.70→0.65
            routing = "high_quality"
            action = "forward_to_matching"
        elif rounded_confidence >= 0.40:  # FINAL PUSH: 0.45→0.40 - very permissive
            routing = "medium_quality"
            action = "manual_review"

        # Contradiction-aware routing guardrail:
        # any explicit mismatch should not be auto-forwarded as high quality.
        mismatch_set = set(mismatch_types)
        has_any_mismatch = bool(mismatch_set)
        has_severe_mismatch = bool(mismatch_set & {"item", "brand"})

        if has_any_mismatch and routing == "high_quality":
            routing = "medium_quality"
            action = "manual_review"

        # Severe contradictions (item/brand) should never appear better than low quality.
        if has_severe_mismatch and routing != "low_quality":
            routing = "low_quality"
            action = "return_for_improvement"

        return {
            "overall_confidence": rounded_confidence,
            "raw_confidence": round(overall_confidence, 2),
            "calibration_applied": calibration_applied,
            "routing": routing,
            "action": action,
            "individual_scores": {k: round(v, 3) for k, v in individual_scores.items()},
            "cross_modal_scores": {k: round(v, 3) for k, v in cross_modal_scores.items()},
            "active_weights": active_weights, # Return weights for transparency
            "penalties": {
                "mismatch_penalty": round(penalties["mismatch_penalty"], 3),
                "applied_reasons": penalties["applied_reasons"],
            }
        }
    
    # ------------------------------------------------------------------ #
    # Adaptive Threshold Methods
    # ------------------------------------------------------------------ #
    def get_adaptive_thresholds(self, item_category: str) -> Dict[str, Any]:
        """
        Get validation thresholds based on item category.
        
        Different item types have different validation requirements:
        - Electronics need clearer images (model numbers are small)
        - Clothing just needs color/style visibility
        - Documents need high text completeness
        
        Args:
            item_category: Category of the lost/found item
            
        Returns:
            Dict with threshold values for each validation component
        """
        category_lower = item_category.lower() if item_category else "default"
        
        # Try exact match first
        if category_lower in self.CATEGORY_THRESHOLDS:
            thresholds = self.CATEGORY_THRESHOLDS[category_lower].copy()
            thresholds["category_matched"] = category_lower
            return thresholds
        
        # Try to match to a broader category
        category_mapping = {
            # Electronics
            "iphone": "phone",
            "samsung": "phone",
            "smartphone": "phone",
            "mobile": "phone",
            "cellphone": "phone",
            "macbook": "laptop",
            "notebook": "laptop",
            "tablet": "electronics",
            "ipad": "electronics",
            "camera": "electronics",
            "headphones": "electronics",
            "airpods": "electronics",
            "watch": "electronics",
            "smartwatch": "electronics",
            # Accessories
            "keys": "accessories",
            "glasses": "accessories",
            "sunglasses": "accessories",
            "umbrella": "accessories",
            "charger": "accessories",
            # Bags
            "backpack": "bag",
            "purse": "bag",
            "handbag": "bag",
            "suitcase": "bag",
            "luggage": "bag",
            # Documents
            "passport": "documents",
            "id": "documents",
            "license": "documents",
            "card": "documents",
            # Jewelry
            "ring": "jewelry",
            "necklace": "jewelry",
            "bracelet": "jewelry",
            "earring": "jewelry",
            # Clothing
            "jacket": "clothing",
            "coat": "clothing",
            "shirt": "clothing",
            "hat": "clothing",
            "scarf": "clothing",
        }
        
        mapped_category = category_mapping.get(category_lower, "default")
        thresholds = self.CATEGORY_THRESHOLDS.get(
            mapped_category, 
            self.CATEGORY_THRESHOLDS["default"]
        ).copy()
        thresholds["category_matched"] = mapped_category
        thresholds["original_category"] = category_lower
        
        return thresholds

    def validate_with_adaptive_thresholds(
        self,
        image_result: Optional[Dict],
        text_result: Optional[Dict],
        voice_result: Optional[Dict],
        cross_modal_results: Optional[Dict],
        item_category: str = "default"
    ) -> Dict[str, Any]:
        """
        Validate inputs using category-specific thresholds.
        
        This provides more nuanced validation where, for example,
        a slightly blurry photo of a distinctive red bag might pass,
        but the same quality photo of a silver iPhone would fail.
        
        Args:
            image_result: Image validation results
            text_result: Text validation results
            voice_result: Voice validation results
            cross_modal_results: Cross-modal consistency results
            item_category: Category of the item being validated
            
        Returns:
            Dict with threshold-adjusted validation results
        """
        thresholds = self.get_adaptive_thresholds(item_category)
        
        # Check each component against category-specific thresholds
        validations = {
            "image_passes": False,
            "text_passes": False,
            "voice_passes": False,
            "clip_passes": False,
            "all_pass": False,
            "thresholds_used": thresholds,
            "feedback": []
        }
        
        # Image validation
        if image_result:
            image_score = image_result.get("overall_score", 0) / 100  # Normalize to 0-1
            validations["image_passes"] = image_score >= thresholds["image_quality"]
            validations["image_score"] = round(image_score, 2)
            validations["image_threshold"] = thresholds["image_quality"]
            
            if not validations["image_passes"]:
                diff = thresholds["image_quality"] - image_score
                validations["feedback"].append(
                    f"Image quality ({image_score:.0%}) is below the {item_category} "
                    f"threshold ({thresholds['image_quality']:.0%}). "
                    f"Need {diff:.0%} improvement."
                )
        
        # Text validation
        if text_result:
            text_score = text_result.get("overall_score", 0)
            if text_score > 1:
                text_score = text_score / 100  # Handle percentage format
            validations["text_passes"] = text_score >= thresholds["text_completeness"]
            validations["text_score"] = round(text_score, 2)
            validations["text_threshold"] = thresholds["text_completeness"]
            
            if not validations["text_passes"]:
                validations["feedback"].append(
                    f"Text completeness ({text_score:.0%}) needs more detail for {item_category}. "
                    f"Target: {thresholds['text_completeness']:.0%}."
                )
        
        # Voice validation
        if voice_result:
            voice_score = voice_result.get("overall_score", 0)
            validations["voice_passes"] = voice_score >= thresholds["voice_quality"]
            validations["voice_score"] = round(voice_score, 2)
            validations["voice_threshold"] = thresholds["voice_quality"]
            
            if not validations["voice_passes"] and voice_score > 0:
                validations["feedback"].append(
                    f"Voice quality needs improvement. Try recording in a quieter environment."
                )
        
        # CLIP similarity
        if cross_modal_results and "image_text" in cross_modal_results:
            clip_score = cross_modal_results["image_text"].get("similarity", 0)
            validations["clip_passes"] = clip_score >= thresholds["clip_similarity"]
            validations["clip_score"] = round(clip_score, 2)
            validations["clip_threshold"] = thresholds["clip_similarity"]
            
            if not validations["clip_passes"] and clip_score > 0:
                validations["feedback"].append(
                    f"Image and text don't quite match. Make sure your description "
                    f"accurately describes what's shown in the photo."
                )
        
        # Determine overall pass/fail
        required_passes = []
        if image_result:
            required_passes.append(validations["image_passes"])
        if text_result:
            required_passes.append(validations["text_passes"])
        
        validations["all_pass"] = all(required_passes) if required_passes else False
        
        if validations["all_pass"]:
            validations["feedback"] = [
                f"All quality checks passed for {item_category}! "
                f"Your submission meets the requirements."
            ]
        
        return validations

    def suggest_improvements(
        self,
        validation_result: Dict,
        item_category: str = "default"
    ) -> List[str]:
        """
        Generate specific improvement suggestions based on validation gaps.
        
        Args:
            validation_result: Results from validate_with_adaptive_thresholds
            item_category: Category of the item
            
        Returns:
            List of actionable improvement suggestions
        """
        suggestions = []
        thresholds = self.get_adaptive_thresholds(item_category)
        
        # Image improvements
        if not validation_result.get("image_passes", True):
            score = validation_result.get("image_score", 0)
            if score < 0.5:
                suggestions.append(
                    "📷 Your photo is too blurry. Try holding the camera steady, "
                    "or use better lighting."
                )
            elif score < thresholds["image_quality"]:
                suggestions.append(
                    f"📷 For {item_category}, we need a clearer photo. "
                    f"Try photographing the {item_category} from multiple angles."
                )
        
        # Text improvements
        if not validation_result.get("text_passes", True):
            score = validation_result.get("text_score", 0)
            suggestions.append(
                f"✏️ Please add more details to your description. "
                f"Include: brand, color, distinguishing marks, and where you last saw it."
            )
        
        # CLIP improvements
        if not validation_result.get("clip_passes", True):
            suggestions.append(
                "🔗 Your photo and description don't quite match. "
                "Make sure the photo shows the item you're describing."
            )
        
        # Voice improvements
        if not validation_result.get("voice_passes", True):
            score = validation_result.get("voice_score", 0)
            if score > 0:
                suggestions.append(
                    "🎤 Voice recording quality could be better. "
                    "Try recording in a quieter environment and speak clearly."
                )
        
        return suggestions

    # ------------------------------------------------------------------ #
    # Calibration Methods (Research Enhancement)
    # ------------------------------------------------------------------ #
    def train_calibrator(self, confidences: list, outcomes: list, method: str = "isotonic") -> bool:
        """
        Train the confidence calibrator on collected data.
        
        Args:
            confidences: List of predicted confidence scores
            outcomes: List of binary outcomes (1=correct, 0=incorrect)
            method: Calibration method ('temperature', 'isotonic', 'platt')
        
        Returns:
            True if training succeeded
        
        Example:
            # Collect from validation history
            confidences = [0.85, 0.92, 0.67, 0.78, ...]
            outcomes = [1, 1, 0, 1, ...]  # 1=correct prediction, 0=wrong
            engine.train_calibrator(confidences, outcomes)
        """
        if not ConfidenceCalibrator:
            logger.error("ConfidenceCalibrator not available")
            return False
        
        try:
            import numpy as np
            conf_array = np.array(confidences)
            out_array = np.array(outcomes)
            
            if len(conf_array) < 30:
                logger.warning(f"Only {len(conf_array)} samples, need 30+ for reliable calibration")
            
            self.confidence_calibrator = ConfidenceCalibrator(method=method)
            self.confidence_calibrator.fit(conf_array, out_array)
            self._calibrator_fitted = True
            
            # Log calibration improvement
            metrics = self.confidence_calibrator.evaluate(conf_array, out_array)
            logger.info(f"Calibrator trained: ECE = {metrics.ece:.4f}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to train calibrator: {e}")
            return False
    
    def load_calibrator(self, path: str = "models/calibrator_isotonic.pkl") -> bool:
        """
        Load a pre-trained calibrator from disk.
        
        Args:
            path: Path to saved calibrator file
        
        Returns:
            True if loading succeeded
        """
        if not ConfidenceCalibrator:
            logger.error("ConfidenceCalibrator not available")
            return False
        
        try:
            self.confidence_calibrator = ConfidenceCalibrator.load(path)
            self._calibrator_fitted = self.confidence_calibrator.is_fitted
            logger.info(f"Calibrator loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load calibrator: {e}")
            return False
    
    def save_calibrator(self, path: str = "models/calibrator_isotonic.pkl") -> bool:
        """
        Save the trained calibrator to disk.
        
        Args:
            path: Path to save calibrator
        
        Returns:
            True if saving succeeded
        """
        if not self.confidence_calibrator or not self._calibrator_fitted:
            logger.error("No fitted calibrator to save")
            return False
        
        try:
            self.confidence_calibrator.save(path)
            return True
        except Exception as e:
            logger.error(f"Failed to save calibrator: {e}")
            return False
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """
        Get calibration statistics.
        
        Returns:
            Dict with calibration info or empty if not calibrated
        """
        if not self.confidence_calibrator or not self._calibrator_fitted:
            return {
                "calibrated": False,
                "message": "Calibrator not trained"
            }
        
        return {
            "calibrated": True,
            "method": self.confidence_calibrator.method,
            "history": self.confidence_calibrator.calibration_history,
        }

