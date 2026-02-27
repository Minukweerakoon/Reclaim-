"""
PHASE 6: Adaptive Threshold Formula
Implements dynamic thresholds based on multiple context factors:
- θ_adaptive = θ_base × W_completeness × W_quality × W_specificity × W_historical
"""

import logging
from typing import Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveThresholdCalculator:
    """
    Calculates dynamic CLIP validation thresholds based on multiple factors.
    
    Formula: θ_adaptive = θ_base × W_c × W_q × W_s × W_h
    where:
        θ_base = Category default threshold (0.5-0.95)
        W_c = Completeness factor (0.9-1.1) - based on # of modalities
        W_q = Quality factor (0.85-1.0) - based on image sharpness
        W_s = Specificity factor (0.90-1.05) - based on item category distinctiveness
        W_h = Historical factor (0.95-1.05) - based on learned accuracy
    """
    
    # Base thresholds by item category
    CATEGORY_THRESHOLDS = {
        "phone": 0.75,
        "laptop": 0.80,
        "watch": 0.78,
        "jewelry": 0.75,
        "wallet": 0.70,
        "keys": 0.68,
        "bag": 0.65,
        "backpack": 0.65,
        "shoe": 0.70,
        "clothing": 0.55,
        "glasses": 0.70,
        "headphones": 0.72,
        "charger": 0.60,
        "book": 0.62,
        "pen": 0.50,
        "card": 0.50,
        "unknown": 0.60
    }
    
    # Item distinctiveness (how easy to identify from images)
    ITEM_DISTINCTIVENESS = {
        "phone": 0.95,        # Very distinctive
        "laptop": 0.95,
        "watch": 0.90,
        "jewelry": 0.85,      # Can be hard to distinguish similar products
        "wallet": 0.80,
        "keys": 0.75,         # Generic looking
        "bag": 0.70,
        "backpack": 0.70,
        "shoe": 0.75,
        "clothing": 0.50,     # Can look similar to many others
        "glasses": 0.80,
        "headphones": 0.85,
        "charger": 0.60,      # Generic looking
        "book": 0.70,
        "pen": 0.40,          # Very generic
        "card": 0.30,         # Very generic
        "unknown": 0.50
    }
    
    def __init__(self):
        self.historical_accuracy: Dict[str, float] = {}  # Track accuracy per category
        self.modality_weights = {
            "text": 0.30,
            "image": 0.50,
            "voice": 0.20
        }
    
    def calculate_completeness_factor(self, num_modalities: int) -> float:
        """
        W_completeness: Adjust threshold based on number of available modalities.
        
        More modalities = we can be stricter (higher threshold)
        Fewer modalities = we should be more relaxed (lower threshold)
        
        Args:
            num_modalities: Number of modalities provided (1-3)
            
        Returns:
            Completeness factor (0.9-1.1)
        """
        if num_modalities == 1:
            return 0.95  # Only one modality, be lenient
        elif num_modalities == 2:
            return 1.00  # Two modalities, standard
        elif num_modalities >= 3:
            return 1.10  # All modalities, can be strict
        else:
            return 0.90  # Fallback
    
    def calculate_quality_factor(self, image_sharpness_score: float) -> float:
        """
        W_quality: Adjust threshold based on image quality.
        
        Poor quality images → lower threshold (more lenient)
        High quality images → higher threshold (stricter)
        
        Args:
            image_sharpness_score: Laplacian variance (typical range 0-300+)
            
        Returns:
            Quality factor (0.85-1.0)
        """
        # Normalize sharpness score to 0-1 range
        # Assuming typical values: 50 (blurry) to 200 (sharp)
        normalized = min(image_sharpness_score / 200.0, 1.0)
        
        # Map to quality factor: 0.85 (blurry) to 1.0 (sharp)
        quality_factor = 0.85 + (normalized * 0.15)
        
        return round(quality_factor, 3)
    
    def calculate_specificity_factor(self, item_category: str) -> float:
        """
        W_specificity: Adjust threshold based on item distinctiveness.
        
        Distinctive items (phones) → higher threshold (can be stricter)
        Generic items (pens) → lower threshold (more lenient)
        
        Args:
            item_category: Item category (e.g., 'phone', 'pen')
            
        Returns:
            Specificity factor (0.90-1.05)
        """
        distinctiveness = self.ITEM_DISTINCTIVENESS.get(item_category.lower(), 0.50)
        
        # Map distinctiveness 0.30-0.95 to factor 0.90-1.05
        # Higher distinctiveness → higher factor (stricter)
        specificity_factor = 0.90 + (distinctiveness * 0.15)
        
        return round(specificity_factor, 3)
    
    def calculate_historical_factor(self, item_category: str, num_validations: int = 0) -> float:
        """
        W_historical: Adjust threshold based on learned accuracy.
        
        If we've validated many items of this type and had high accuracy,
        we learned that our CLIP model works well → can be stricter.
        
        Args:
            item_category: Item category
            num_validations: Number of historical validations for this category
            
        Returns:
            Historical factor (0.95-1.05)
        """
        if item_category.lower() not in self.historical_accuracy:
            # No history yet, use neutral factor
            return 1.00
        
        accuracy = self.historical_accuracy[item_category.lower()]
        
        # If past validations were accurate (>0.8), increase threshold (stricter)
        # If past validations were poor (<0.5), decrease threshold (more lenient)
        if num_validations > 10:  # Only adjust if we have enough data
            historical_factor = 0.95 + (accuracy * 0.10)
        else:
            historical_factor = 0.98 + (accuracy * 0.07)
        
        return round(historical_factor, 3)
    
    def calculate_adaptive_threshold(
        self,
        item_category: str,
        image_sharpness: Optional[float] = None,
        num_modalities: int = 2,
        num_historical_validations: int = 0
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate adaptive CLIP validation threshold.
        
        Formula: θ_adaptive = θ_base × W_c × W_q × W_s × W_h
        
        Args:
            item_category: Item type (e.g., 'phone', 'wallet')
            image_sharpness: Image quality score (Laplacian variance)
            num_modalities: Number of modalities (1-3)
            num_historical_validations: Number of previous validations
            
        Returns:
            Tuple of (adaptive_threshold, factor_breakdown)
        """
        # Get base threshold for category
        base_threshold = self.CATEGORY_THRESHOLDS.get(item_category.lower(), 0.60)
        
        # Calculate individual factors
        w_completeness = self.calculate_completeness_factor(num_modalities)
        w_quality = self.calculate_quality_factor(image_sharpness or 100)
        w_specificity = self.calculate_specificity_factor(item_category)
        w_historical = self.calculate_historical_factor(item_category, num_historical_validations)
        
        # Apply formula: θ_adaptive = θ_base × W_c × W_q × W_s × W_h
        adaptive_threshold = base_threshold * w_completeness * w_quality * w_specificity * w_historical
        
        # Constrain to valid range [0.50, 0.95]
        adaptive_threshold = max(0.50, min(adaptive_threshold, 0.95))
        
        logger.info(
            f"Adaptive Threshold for '{item_category}': "
            f"Base={base_threshold:.2f} × W_c={w_completeness:.2f} × W_q={w_quality:.2f} × "
            f"W_s={w_specificity:.2f} × W_h={w_historical:.2f} = {adaptive_threshold:.3f}"
        )
        
        return round(adaptive_threshold, 3), {
            "base_threshold": base_threshold,
            "w_completeness": w_completeness,
            "w_quality": w_quality,
            "w_specificity": w_specificity,
            "w_historical": w_historical,
            "adaptive_threshold": adaptive_threshold,
            "justification": {
                "completeness": f"Based on {num_modalities} modalities",
                "quality": f"Image sharpness score: {image_sharpness}",
                "specificity": f"Item distinctiveness for {item_category}: {self.ITEM_DISTINCTIVENESS.get(item_category.lower(), 0.5):.2f}",
                "historical": f"Historical validations: {num_historical_validations}"
            }
        }
    
    def record_validation(self, item_category: str, was_accurate: bool) -> None:
        """
        Record validation outcome to update historical accuracy.
        
        Args:
            item_category: Item category
            was_accurate: Whether validation was accurate
        """
        category = item_category.lower()
        
        if category not in self.historical_accuracy:
            self.historical_accuracy[category] = 1.0 if was_accurate else 0.0
        else:
            # Exponential moving average: new_acc = 0.8 * old_acc + 0.2 * new_result
            old_acc = self.historical_accuracy[category]
            new_result = 1.0 if was_accurate else 0.0
            self.historical_accuracy[category] = 0.8 * old_acc + 0.2 * new_result
        
        logger.info(f"Updated historical accuracy for '{category}': {self.historical_accuracy[category]:.2f}")
    
    def validate_with_adaptive_threshold(
        self,
        clip_similarity: float,
        item_category: str,
        image_sharpness: Optional[float] = None,
        num_modalities: int = 2
    ) -> Dict[str, any]:
        """
        Validate CLIP similarity against adaptive threshold.
        
        Args:
            clip_similarity: CLIP cosine similarity score (0-1)
            item_category: Item category
            image_sharpness: Image quality score
            num_modalities: Number of modalities
            
        Returns:
            Dictionary with validation result and explanation
        """
        threshold, factors = self.calculate_adaptive_threshold(
            item_category=item_category,
            image_sharpness=image_sharpness,
            num_modalities=num_modalities
        )
        
        is_valid = clip_similarity >= threshold
        gap = clip_similarity - threshold
        
        return {
            "valid": is_valid,
            "similarity": clip_similarity,
            "adaptive_threshold": threshold,
            "gap": round(gap, 3),
            "confidence": round(min(clip_similarity, 1.0) * 100, 1),
            "factors": factors,
            "recommendation": self._get_recommendation(is_valid, gap, item_category),
            "action": "accept" if is_valid else "review"
        }
    
    def _get_recommendation(self, is_valid: bool, gap: float, item_category: str) -> str:
        """Generate user-friendly recommendation."""
        if is_valid:
            if gap >= 0.15:
                return f"✓ High confidence match for {item_category}. Accept without review."
            else:
                return f"✓ Acceptable match for {item_category}. Can proceed with caution."
        else:
            if gap >= -0.05:
                return f"⚠️ Below threshold for {item_category} by small margin. Manual review recommended."
            else:
                return f"✗ Poor match for {item_category}. Request more information from user."


# Global singleton
_calculator: Optional[AdaptiveThresholdCalculator] = None


def get_adaptive_threshold_calculator() -> AdaptiveThresholdCalculator:
    """Get or create adaptive threshold calculator."""
    global _calculator
    if _calculator is None:
        _calculator = AdaptiveThresholdCalculator()
    return _calculator
