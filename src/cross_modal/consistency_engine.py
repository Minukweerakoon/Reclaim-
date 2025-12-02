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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ConsistencyEngine')

class ConsistencyEngine:
    """An advanced multi-modal consistency validation system integrating text, audio, and image inputs.
    
    This class provides methods to validate consistency across different modalities:
    - Combines CLIP, BERT, and Whisper results into unified consistency scoring
    - Implements voice-text semantic similarity using sentence transformers
    - Validates location and temporal consistency across modalities
    - Creates adaptive confidence scoring based on input quality
    - Provides intelligent routing based on confidence thresholds
    
    The validation pipeline returns structured results in JSON format with detailed breakdown
    of individual and cross-modal scores, routing decisions, and confidence intervals.
    """
    

    
    def __init__(self, enable_logging: bool = True):
        """Initialize the ConsistencyEngine."""
        self.enable_logging = enable_logging
        self.clip_validator = CLIPValidator()
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_similarity_threshold = 0.75
        self.location_keywords = [
            "library",
            "cafeteria",
            "classroom",
            "parking",
            "gym",
            "auditorium",
            "lab",
            "office",
            "hallway",
            "entrance",
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
            similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
            result["similarity"] = similarity
            
            # Determine validity based on threshold
            result["valid"] = similarity >= self.text_similarity_threshold
            
            if result["valid"]:
                result["feedback"] = "Voice and text are semantically consistent"
            else:
                result["feedback"] = f"Voice and text are not well aligned (similarity: {similarity:.2f}, threshold: {self.text_similarity_threshold})"
            
        except Exception as e:
            if getattr(self, 'enable_logging', False):
                logger.error(f"Error during voice-text consistency validation: {str(e)}")
            result["feedback"] = f"Error during voice-text consistency validation: {str(e)}"
        
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
        
        # Weights from specification
        weights = {
            "image_score": 0.25,
            "text_score": 0.25,
            "voice_score": 0.20,
            "clip_similarity": 0.20,
            "voice_text_similarity": 0.10
        }

        # Collect individual scores
        if image_result and image_result.get("valid"):
            individual_scores["image"] = image_result.get("overall_score", 0.0)
        else:
            individual_scores["image"] = 0.0

        if text_result and text_result.get("valid"):
            individual_scores["text"] = text_result.get("overall_score", 0.0)
        else:
            individual_scores["text"] = 0.0

        if voice_result and voice_result.get("valid"):
            individual_scores["voice"] = voice_result.get("overall_score", 0.0)
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

        # Calculate overall confidence
        overall_confidence += individual_scores["image"] * weights["image_score"]
        overall_confidence += individual_scores["text"] * weights["text_score"]
        overall_confidence += individual_scores["voice"] * weights["voice_score"]
        overall_confidence += cross_modal_scores.get("clip_similarity", 0.0) * weights["clip_similarity"]

        voice_text_component = cross_modal_scores.get("voice_text_similarity", 0.0)
        if "context_consistency" in cross_modal_scores:
            context_score = cross_modal_scores["context_consistency"]
            voice_text_component = 0.7 * voice_text_component + 0.3 * context_score

        overall_confidence += voice_text_component * weights["voice_text_similarity"]

        # Determine routing and action
        routing = "low_quality"
        action = "return_for_improvement"
        if overall_confidence >= 0.85:
            routing = "high_quality"
            action = "forward_to_matching"
        elif overall_confidence >= 0.70:
            routing = "medium_quality"
            action = "manual_review"

        return {
            "overall_confidence": round(overall_confidence, 2),
            "routing": routing,
            "action": action,
            "individual_scores": individual_scores,
            "cross_modal_scores": cross_modal_scores
        }
    


