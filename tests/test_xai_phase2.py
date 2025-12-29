"""
Comprehensive tests for Phase 2 XAI enhancements.
Tests AttentionVisualizer, enhanced discrepancies, and API endpoints.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test AttentionVisualizer
def test_attention_visualizer_initialization():
    """Test AttentionVisualizer initializes correctly"""
    from src.cross_modal.attention_visualizer import AttentionVisualizer
    
    visualizer = AttentionVisualizer()
    assert visualizer.output_dir == "uploads/heatmaps"
    assert os.path.exists(visualizer.output_dir)


def test_attention_map_generation():
    """Test attention heatmap generation with mock data"""
    from src.cross_modal.attention_visualizer import AttentionVisualizer
    import numpy as np
    from PIL import Image
    
    # Create test image
    test_image = Image.new('RGB', (224, 224), color='red')
    test_image_path = "test_image_temp.jpg"
    test_image.save(test_image_path)
    
    try:
        visualizer = AttentionVisualizer()
        
        # Mock CLIP model
        class MockCLIPModel:
            pass
        
        result = visualizer.generate_attention_map(
            image_path=test_image_path,
            text="red backpack",
            clip_model=MockCLIPModel()
        )
        
        assert "attention_scores" in result
        assert "explanation" in result
        assert len(result["attention_scores"]) > 0
        
    finally:
        # Cleanup
        if os.path.exists(test_image_path):
            os.remove(test_image_path)


def test_identify_top_regions():
    """Test top region identification"""
    from src.cross_modal.attention_visualizer import AttentionVisualizer
    import numpy as np
    
    visualizer = AttentionVisualizer()
    
    # Create attention map with known pattern
    attention_map = np.random.rand(224, 224)
    attention_map[100:120, 100:120] = 0.95  # High attention in center
    
    top_regions = visualizer._identify_top_regions(attention_map, num_regions=3)
    
    assert len(top_regions) <= 3
    assert all("region" in r and "score" in r for r in top_regions)


# Test Enhanced Discrepancies
def test_brand_mismatch_detection():
    """Test brand mismatch detection"""
    from src.cross_modal.enhanced_discrepancies import check_brand_mismatch
    
    # Case 1: Brand mentioned but not in image
    result = check_brand_mismatch(
        image_result={"ocr_text": ""},
        text_result={"text": "Apple iPhone 15 Pro"}
    )
    
    assert result.get("has_mismatch") == True
    assert "Apple" in result.get("explanation", "").lower() or "apple" in result.get("explanation", "")
    assert result.get("severity") == "medium"
    
    # Case 2: Brand visible in image
    result2 = check_brand_mismatch(
        image_result={"ocr_text": "Apple iPhone"},
        text_result={"text": "Apple iPhone 15"}
    )
    
    assert result2.get("has_mismatch") == False


def test_location_consistency():
    """Test location consistency between text and voice"""
    from src.cross_modal.enhanced_discrepancies import check_location_consistency
    
    # Case 1: Locations mismatch
    result = check_location_consistency(
        text_result={"text": "I lost it in the library", "entities": {"location_mentions": ["library"]}},
        voice_result={"transcription": {"transcription": "I found it in the cafeteria"}}
    )
    
    assert result.get("has_mismatch") == True
    assert "library" in result.get("explanation", "").lower()
    assert "cafeteria" in result.get("explanation", "").lower()
    
    # Case 2: Locations match
    result2 = check_location_consistency(
        text_result={"text": "library", "entities": {"location_mentions": ["library"]}},
        voice_result={"transcription": {"transcription": "library"}}
    )
    
    assert result2.get("has_mismatch") == False


def test_condition_mismatch():
    """Test condition mismatch detection"""
    from src.cross_modal.enhanced_discrepancies import check_condition_mismatch
    
    # Case 1: Says "new" but image quality low
    result = check_condition_mismatch(
        image_result={"overall_score": 0.5, "sharpness": {"score": 70}},
        text_result={"text": "brand new laptop in mint condition"}
    )
    
    assert result.get("has_mismatch") == True
    assert "new" in result.get("explanation", "").lower()
    assert result.get("severity") == "medium"
    
    # Case 2: High quality image, says "new"
    result2 = check_condition_mismatch(
        image_result={"overall_score": 0.9, "sharpness": {"score": 95}},
        text_result={"text": "brand new item"}
    )
    
    assert result2.get("has_mismatch") == False


def test_extract_brands():
    """Test brand extraction from text"""
    from src.cross_modal.enhanced_discrepancies import _extract_brands
    
    text1 = "I have an Apple iPhone and Samsung Galaxy"
    brands1 = _extract_brands(text1)
    assert "apple" in brands1 or "Apple" in [b.lower() for b in brands1]
    assert "samsung" in brands1 or "Samsung" in [b.lower() for b in brands1]
    
    text2 = "Just a regular phone"
    brands2 = _extract_brands(text2)
    # May find capitalized words but should handle gracefully
    assert isinstance(brands2, list)


def test_extract_condition():
    """Test condition extraction"""
    from src.cross_modal.enhanced_discrepancies import _extract_condition
    
    assert _extract_condition("brand new laptop") == "new"
    assert _extract_condition("used phone in good condition") == "used"
    assert _extract_condition("excellent condition") == "good"
    assert _extract_condition("just a regular item") is None


# Test API Endpoints (requires running server)
@pytest.mark.skip(reason="Requires running server")
def test_attention_endpoint():
    """Test /api/xai/attention endpoint"""
    import requests
    from io import BytesIO
    from PIL import Image
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = requests.post(
        "http://localhost:8000/api/xai/attention",
        files={"image_file": ("test.jpg", img_bytes, "image/jpeg")},
        data={"text": "red backpack"},
        headers={"X-API-Key": "test_api_key_12345"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "attention_scores" in data or "error" in data


@pytest.mark.skip(reason="Requires running server")
def test_enhanced_explain_endpoint():
    """Test /api/xai/explain-enhanced endpoint"""
    import requests
    
    response = requests.post(
        "http://localhost:8000/api/xai/explain-enhanced",
        json={
            "image_result": {"ocr_text": ""},
            "text_result": {"text": "Apple iPhone"},
            "include_discrepancies": True
        },
        headers={"X-API-Key": "test_api_key_12345"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "has_discrepancy" in data


# Integration tests
def test_full_xai_workflow():
    """Test complete XAI workflow"""
    from src.cross_modal.enhanced_discrepancies import (
        check_brand_mismatch,
        check_location_consistency,
        check_condition_mismatch
    )
    
    # Simulate validation results
    image_result = {
        "ocr_text": "",
        "overall_score": 0.8,
        "sharpness": {"score": 85}
    }
    
    text_result = {
        "text": "Nike brand new shoes found in library",
        "entities": {"location_mentions": ["library"]}
    }
    
    voice_result = {
        "transcription": {"transcription": "found shoes in cafeteria"}
    }
    
    # Run all checks
    brand_result = check_brand_mismatch(image_result, text_result)
    location_result = check_location_consistency(text_result, voice_result)
    condition_result = check_condition_mismatch(image_result, text_result)
    
    # Should detect brand and location mismatches
    assert brand_result.get("has_mismatch") == True  # Nike not visible
    assert location_result.get("has_mismatch") == True  # library vs cafeteria
    assert condition_result.get("has_mismatch") == False  # Good quality, "new" is OK


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
