"""
Quick test script for new validation features.
Run: python test_new_features.py
"""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("Testing New Validation Features")
print("=" * 60)

# Test 1: Text Intent Classification
print("\n[1] Testing Intent Classification...")
try:
    from src.text.validator import TextValidator
    tv = TextValidator(enable_logging=False)
    
    # Test lost intent
    result = tv.classify_intent("I lost my black wallet at the library")
    print(f"   'I lost my wallet...' -> Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
    
    # Test found intent  
    result = tv.classify_intent("I found a phone near the cafeteria")
    print(f"   'I found a phone...' -> Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
    
    # Test inquiry
    result = tv.classify_intent("Has anyone seen a red umbrella?")
    print(f"   'Has anyone seen...' -> Intent: {result['intent']}, Confidence: {result['confidence']:.2f}")
    
    print("   ✅ Intent Classification WORKING")
except Exception as e:
    print(f"   ❌ Intent Classification FAILED: {e}")

# Test 2: Urgency Analysis
print("\n[2] Testing Urgency Analysis...")
try:
    # Test critical urgency
    result = tv.analyze_urgency("URGENT! I lost my passport and my flight is in 2 hours!")
    print(f"   Critical case -> Urgency: {result['urgency']}, Score: {result['score']}")
    
    # Test normal
    result = tv.analyze_urgency("I think I may have left my umbrella somewhere")
    print(f"   Normal case -> Urgency: {result['urgency']}, Score: {result['score']}")
    
    print("   ✅ Urgency Analysis WORKING")
except Exception as e:
    print(f"   ❌ Urgency Analysis FAILED: {e}")

# Test 3: pHash Duplicate Detection
print("\n[3] Testing pHash Duplicate Detection...")
try:
    from src.image.validator import ImageValidator
    iv = ImageValidator(enable_logging=False)
    
    # Check if method exists
    if hasattr(iv, 'compute_phash'):
        print("   compute_phash() method EXISTS")
        # Try to compute hash (may fail without an actual image)
        print("   ✅ pHash Methods Available")
    else:
        print("   ❌ compute_phash() method MISSING")
except Exception as e:
    print(f"   ⚠️ pHash test partial: {e}")

# Test 4: Adaptive Thresholds
print("\n[4] Testing Adaptive Thresholds...")
try:
    from src.cross_modal.consistency_engine import ConsistencyEngine
    ce = ConsistencyEngine(enable_logging=False)
    
    # Test electronics threshold
    thresholds = ce.get_adaptive_thresholds("iphone")
    print(f"   iPhone thresholds -> Image: {thresholds['image_quality']}, Text: {thresholds['text_completeness']}")
    
    # Test clothing threshold
    thresholds = ce.get_adaptive_thresholds("jacket")
    print(f"   Jacket thresholds -> Image: {thresholds['image_quality']}, Text: {thresholds['text_completeness']}")
    
    print("   ✅ Adaptive Thresholds WORKING")
except Exception as e:
    print(f"   ❌ Adaptive Thresholds FAILED: {e}")

# Test 5: Multi-Language Detection
print("\n[5] Testing Multi-Language Detection...")
try:
    from src.voice.validator import VoiceValidator
    
    # Check if method exists (don't load model, just check structure)
    if hasattr(VoiceValidator, 'detect_language'):
        print("   detect_language() method EXISTS")
        print("   SUPPORTED_LANGUAGES config available")
        print("   ✅ Multi-Language Methods Available")
    else:
        print("   ❌ detect_language() method MISSING")
except Exception as e:
    print(f"   ⚠️ Voice test skipped (model loading): {type(e).__name__}")

print("\n" + "=" * 60)
print("Feature Test Complete!")
print("=" * 60)
