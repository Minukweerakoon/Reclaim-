"""
Test script for AI-Driven Spatial-Temporal Validation
Tests the enhanced system with novel items not in the pre-programmed list.
"""

import sys
sys.path.append('.')

from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator

def test_ai_driven_validation():
    """Test AI-driven validation with various item types."""
    
    validator = get_spatial_temporal_validator()
    
    # Test cases: mix of known, novel, and semantically similar items
    test_cases = [
        # Known items (should use direct match)
        ("laptop", "library", "afternoon"),
        
        # Novel items (should use LLM + Semantic)
        ("VR headset", "library", "afternoon"),
        ("gaming controller", "gym", "evening"),
        ("vintage camera", "cafeteria", "noon"),
        ("kindle e-reader", "library", "morning"),
        ("drone", "parking", "noon"),
        
        # Semantic variations
        ("MacBook Pro", "library", "afternoon"),
        ("AirPods Max", "gym", "morning"),
        ("Nintendo Switch", "hostel", "night"),
    ]
    
    print("=" * 80)
    print("AI-DRIVEN SPATIAL-TEMPORAL VALIDATION TESTS")
    print("=" * 80)
    print()
    
    for item, location, time in test_cases:
        print(f"Testing: {item} at {location} during {time}")
        print("-" * 80)
        
        try:
            result = validator.calculate_plausibility(item, location, time)
            
            print(f"  Normalized: {result['normalized_inputs']['item']}")
            print(f"  Score: {result['plausibility_score']:.2f}")
            print(f"  Valid: {'✓' if result['valid'] else '✗'}")
            print(f"  Confidence: {result['confidence_level']}")
            print(f"  Explanation: {result['explanation']}")
            
            if result['suggestions']:
                print("  Suggestions:")
                for suggestion in result['suggestions']:
                    print(f"    - {suggestion}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print()
    
    print("=" * 80)
    print("AI COMPONENT STATS")
    print("=" * 80)
    
    # Check if AI components are loaded
    print(f"  LLM Extractor: {'✓ Loaded' if validator.llm_extractor else '✗ Not loaded'}")
    print(f"  Semantic Matcher: {'✓ Loaded' if validator.semantic_matcher else '✗ Not loaded'}")
    
    if validator.semantic_matcher:
        num_known_items = len(validator.semantic_matcher.known_items_embeddings)
        print(f"  Known Items: {num_known_items}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    test_ai_driven_validation()
