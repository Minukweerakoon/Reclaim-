"""
Test Spatial-Temporal Validator Robustness
==========================================

Test the fixes for location and item recognition.
"""

import sys
sys.path.append('c:\\Users\\16473\\Desktop\\multimodel-validation')

from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator

def test_car_park_recognition():
    """Test that 'car park' is now recognized as 'parking'."""
    validator = get_spatial_temporal_validator()
    
    print("\n" + "="*60)
    print("TEST 1: Car Park Location Recognition")
    print("="*60)
    
    test_locations = [
        "car park",
        "parking lot",
        "parking area",
        "parking space",
        "vehicle parking",
        "garage"
    ]
    
    for location in test_locations:
        normalized = validator.normalize_location(location)
        status = "✓ PASS" if normalized == "parking" else "✗ FAIL"
        print(f"{status}: '{location}' → '{normalized}'")
    
    print()

def test_headset_recognition():
    """Test that 'headset' is recognized as 'headphones'."""
    validator = get_spatial_temporal_validator()
    
    print("\n" + "="*60)
    print("TEST 2: Headset/Headphones Item Recognition")
    print("="*60)
    
    test_items = [
        "headset",
        "headphones",
        "wireless headphones",
        "bluetooth headset",
        "airpods",
        "earbuds"
    ]
    
    for item in test_items:
        normalized = validator.normalize_item(item)
        status = "✓ PASS" if normalized == "headphones" else "✗ FAIL"
        print(f"{status}: '{item}' → '{normalized}'")
    
    print()

def test_actual_scenario():
    """Test the actual user scenario: headphones at car park."""
    validator = get_spatial_temporal_validator()
    
    print("\n" + "="*60)
    print("TEST 3: Actual Scenario - Headphones at Car Park")
    print("="*60)
    
    result = validator.calculate_plausibility(
        item="black headset",
        location="car park",
        time="late_night"
    )
    
    print(f"\nInput:")
    print(f"  Item: 'black headset'")
    print(f"  Location: 'car park'")
    print(f"  Time: 'late_night'")
    
    print(f"\nNormalized:")
    print(f"  Item: {result['normalized_inputs']['item']}")
    print(f"  Location: {result['normalized_inputs']['location']}")
    print(f"  Time: {result['normalized_inputs']['time']}")
    
    print(f"\nResults:")
    print(f"  Plausibility Score: {result['plausibility_score']:.2%}")
    print(f"  Location Probability: {result['location_probability']:.2%}")
    if result['time_probability']:
        print(f"  Time Probability: {result['time_probability']:.2%}")
    print(f"  Confidence Level: {result['confidence_level']}")
    print(f"  Valid: {result['valid']}")
    
    print(f"\nExplanation:")
    print(f"  {result['explanation']}")
    
    # Validation
    print(f"\nValidation:")
    if result['normalized_inputs']['location'] == 'parking':
        print(f"  ✓ PASS: Location correctly normalized to 'parking'")
    else:
        print(f"  ✗ FAIL: Location is '{result['normalized_inputs']['location']}', expected 'parking'")
    
    if result['normalized_inputs']['item'] == 'headphones':
        print(f"  ✓ PASS: Item correctly normalized to 'headphones'")
    else:
        print(f"  ✗ FAIL: Item is '{result['normalized_inputs']['item']}', expected 'headphones'")
    
    if result['plausibility_score'] >= 0.30:
        print(f"  ✓ PASS: Plausibility score is reasonable ({result['plausibility_score']:.2%})")
    else:
        print(f"  ⚠ WARN: Plausibility score is low ({result['plausibility_score']:.2%})")
    
    print()

def main():
    """Run all robustness tests."""
    print("\n" + "="*60)
    print("SPATIAL-TEMPORAL VALIDATOR ROBUSTNESS TESTS")
    print("="*60)
    
    test_car_park_recognition()
    test_headset_recognition()
    test_actual_scenario()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
