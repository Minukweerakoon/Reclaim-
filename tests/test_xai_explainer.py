"""
Tests for XAI Explainer Module
"""
import pytest
from src.cross_modal.xai_explainer import XAIExplainer

@pytest.fixture
def explainer():
    """Create an XAI explainer instance."""
    return XAIExplainer()

def test_object_mismatch_detection(explainer):
    """Test detection of object mismatches between image and text."""
    image_result = {
        "detection": {
            "class": "wallet",
            "confidence": 0.92
        }
    }
    
    text_result = {
        "text": "I lost my black iPhone 13 in the library",
        "entities": {
            "item_mentions": ["iphone"],
            "color_mentions": ["black"]
        }
    }
    
    explanation = explainer.generate_explanation(
        image_result=image_result,
        text_result=text_result
    )
    
    assert explanation["has_discrepancy"] == True
    assert explanation["discrepancy_type"] == "object_mismatch"
    assert "wallet" in explanation["explanation"].lower()
    assert "iphone" in explanation["explanation"].lower()
    assert explanation["severity"] == "high"

def test_color_mismatch_detection(explainer):
    """Test detection of color mismatches."""
    image_result = {
        "dominant_color": "blue"
    }
    
    text_result = {
        "text": "Lost my red backpack",
        "entities": {
            "color_mentions": ["red"],
            "item_mentions": ["backpack"]
        }
    }
    
    explanation = explainer.generate_explanation(
        image_result=image_result,
        text_result=text_result
    )
    
    assert explanation["has_discrepancy"] == True
    assert explanation["discrepancy_type"] == "color_mismatch"
    assert "blue" in explanation["explanation"].lower()
    assert "red" in explanation["explanation"].lower()

def test_no_discrepancy(explainer):
    """Test when inputs are consistent."""
    image_result = {
        "detection": {
            "class": "phone",
            "confidence": 0.95
        },
        "dominant_color": "black"
    }
    
    text_result = {
        "text": "Lost my black phone",
        "entities": {
            "item_mentions": ["phone"],
            "color_mentions": ["black"]
        }
    }
    
    cross_modal_results = {
        "image_text": {
            "valid": True,
            "similarity": 0.92
        }
    }
    
    explanation = explainer.generate_explanation(
        image_result=image_result,
        text_result=text_result,
        cross_modal_results=cross_modal_results
    )
    
    assert explanation["has_discrepancy"] == False

def test_clip_similarity_low(explainer):
    """Test explanation for low CLIP similarity."""
    cross_modal_results = {
        "image_text": {
            "valid": False,
            "similarity": 0.45
        }
    }
    
    explanation = explainer.generate_explanation(
        cross_modal_results=cross_modal_results
    )
    
    assert explanation["has_discrepancy"] == True
    assert explanation["discrepancy_type"] == "semantic_mismatch"
    assert "45%" in explanation["explanation"]

def test_summary_message(explainer):
    """Test summary message generation."""
    explanation = {
        "has_discrepancy": True,
        "severity": "high",
        "explanation": "Object mismatch detected"
    }
    
    message = explainer.get_summary_message(explanation)
    
    assert "ERROR" in message
    assert "Object mismatch" in message

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
