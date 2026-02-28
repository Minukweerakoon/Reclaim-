import sys
import os
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cross_modal.consistency_engine import ConsistencyEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestAdaptiveScoring")

def test_adaptive_scoring():
    engine = ConsistencyEngine(enable_logging=True)
    
    # Mock Results
    perfect_image = {"valid": True, "overall_score": 0.95}
    perfect_text = {"valid": True, "overall_score": 0.95}
    missing_voice = {"valid": False, "overall_score": 0.0}
    
    # Mock Cross-Modal Results
    cross_modal_results = {
        "image_text": {"similarity": 0.90}, # High alignment
        "voice_text": {"similarity": 0.0},
        "context": {"score": 0.0}
    }
    
    logger.info("Testing Adaptive Scoring with Image + Text (No Voice)...")
    
    result = engine.calculate_overall_confidence(
        image_result=perfect_image,
        text_result=perfect_text,
        voice_result=missing_voice,
        cross_modal_results=cross_modal_results
    )
    
    logger.info(f"Overall Confidence: {result['overall_confidence']}")
    logger.info(f"Routing: {result['routing']}")
    logger.info(f"Active Weights: {result['active_weights']}")
    
    # Verification
    # With old weights: 0.95*0.25 + 0.95*0.25 + 0*0.2 + 0.90*0.2 + 0 = 0.2375 + 0.2375 + 0.18 = 0.655 -> Low Quality
    # With adaptive weights (No Voice): 
    # Image(0.35), Text(0.35), CLIP(0.30)
    # 0.95*0.35 + 0.95*0.35 + 0.90*0.30 = 0.3325 + 0.3325 + 0.27 = 0.935 -> High Quality
    
    if result['overall_confidence'] > 0.85:
        logger.info("SUCCESS: Adaptive scoring correctly boosted confidence for partial high-quality input.")
    else:
        logger.error(f"FAILURE: Confidence {result['overall_confidence']} is too low. Adaptive scoring might not be working.")

if __name__ == "__main__":
    test_adaptive_scoring()
