"""
Unit tests for image validation and object detection.
Tests YOLO-primary strategy, ViT fallback, and class mapping.
"""
import pytest
import os
from pathlib import Path
from src.image.validator import ImageValidator


@pytest.fixture
def validator():
    """Create ImageValidator instance for testing."""
    return ImageValidator(enable_logging=False)


@pytest.fixture
def sample_images_dir():
    """Path to sample test images."""
    return Path(__file__).parent / "fixtures" / "images"


class TestYOLOClassMapping:
    """Test YOLO to Lost & Found category mapping."""
    
    def test_phone_mapping(self, validator):
        """Test cell phone maps to 'phone'."""
        result = validator._map_yolo_class("cell phone")
        assert result == "phone"
    
    def test_wallet_mapping(self, validator):
        """Test handbag maps to 'wallet' (not backpack)."""
        result = validator._map_yolo_class("handbag")
        assert result == "wallet"
    
    def test_laptop_mapping(self, validator):
        """Test laptop maps correctly."""
        result = validator._map_yolo_class("laptop")
        assert result == "laptop"
    
    def test_backpack_mapping(self, validator):
        """Test backpack maps correctly."""
        result = validator._map_yolo_class("backpack")
        assert result == "backpack"
    
    def test_unknown_class_passthrough(self, validator):
        """Test unknown classes pass through unchanged."""
        result = validator._map_yolo_class("unknown_item")
        assert result == "unknown_item"


class TestObjectDetection:
    """Test object detection with YOLO-primary strategy."""
    
    @pytest.mark.skip(reason="Requires test images")
    def test_yolo_detects_phone(self, validator, sample_images_dir):
        """Test YOLO detects phones correctly."""
        phone_image = sample_images_dir / "phone.jpg"
        if not phone_image.exists():
            pytest.skip("Test image not available")
        
        result = validator.detect_objects(str(phone_image))
        
        assert result["valid"] == True
        assert result["model"] == "YOLOv11-Primary"
        assert any("phone" in d["class"].lower() for d in result["detections"])
    
    @pytest.mark.skip(reason="Requires test images")
    def test_vit_fallback_when_yolo_fails(self, validator, sample_images_dir):
        """Test ViT activates when YOLO finds nothing."""
        # Image of keys (YOLO typically can't detect)
        keys_image = sample_images_dir / "keys.jpg"
        if not keys_image.exists():
            pytest.skip("Test image not available")
        
        result = validator.detect_objects(str(keys_image))
        
        # Should fall back to ViT
        assert result["model"] == "ViT-Fallback"
    
    def test_detection_returns_valid_structure(self, validator):
        """Test detection result has correct structure."""
        # This will fail gracefully with no image
        result = validator.detect_objects("nonexistent.jpg")
        
        # Should still return proper structure
        assert "valid" in result
        assert "confidence" in result
        assert "detections" in result
        assert "model" in result


class TestImageValidation:
    """Test full image validation pipeline."""
    
    @pytest.mark.skip(reason="Requires test images")
    def test_validate_image_with_text_hint(self, validator, sample_images_dir):
        """Test image validation with text hint."""
        phone_image = sample_images_dir / "phone.jpg"
        if not phone_image.exists():
            pytest.skip("Test image not available")
        
        result = validator.validate_image(str(phone_image), text="iPhone 15")
        
        assert "valid" in result
        assert "overall_score" in result
        assert "objects" in result
    
    def test_validate_nonexistent_image(self, validator):
        """Test validation handles missing files gracefully."""
        result = validator.validate_image("nonexistent.jpg")
        
        assert result["valid"] == False
        assert "sharpness" in result
        assert result["sharpness"]["valid"] == False


class TestFileValidation:
    """Test file validation (size, format)."""
    
    def test_file_size_check(self, validator):
        """Test file size validation."""
        # This tests the validation logic
        result = validator.validate_file("test.jpg")
        
        # Should check for file existence
        assert "valid" in result
        assert "message" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
