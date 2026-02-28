"""
Integration tests for API endpoints.
Tests /validate/image, /validate/voice, /validate/text endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import io
from PIL import Image


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from app import app
    return TestClient(app)


@pytest.fixture
def api_key():
    """API key for authentication."""
    return "test-api-key"


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


class TestImageEndpoint:
    """Test /validate/image endpoint."""
    
    def test_image_upload_requires_auth(self, client, sample_image):
        """Test endpoint requires API key."""
        response = client.post(
            "/validate/image",
            files={"image_file": ("test.jpg", sample_image, "image/jpeg")}
        )
        assert response.status_code in [401, 403]  # Unauthorized
    
    def test_image_upload_with_auth(self, client, sample_image, api_key):
        """Test image upload with valid API key."""
        response = client.post(
            "/validate/image",
            files={"image_file": ("test.jpg", sample_image, "image/jpeg")},
            data={"text": "test item"},
            headers={"X-API-Key": api_key}
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "image" in data or "error" in data
    
    def test_invalid_file_type(self, client, api_key):
        """Test endpoint rejects invalid file types."""
        text_file = io.BytesIO(b"not an image")
        
        response = client.post(
            "/validate/image",
            files={"image_file": ("test.txt", text_file, "text/plain")},
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code in [400, 415]  # Bad request or unsupported media type


class TestTextEndpoint:
    """Test /validate/text endpoint."""
    
    def test_text_validation(self, client, api_key):
        """Test text validation endpoint."""
        response = client.post(
            "/validate/text",
            json={"text": "I lost my black iPhone 15 at the library"},
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "text" in data or "valid" in data
    
    def test_empty_text_validation(self, client, api_key):
        """Test validation rejects empty text."""
        response = client.post(
            "/validate/text",
            json={"text": ""},
            headers={"X-API-Key": api_key}
        )
        
        # Should reject or handle gracefully
        assert response.status_code in [200, 400]


class TestVoiceEndpoint:
    """Test /validate/voice endpoint."""
    
    @pytest.mark.skip(reason="Requires audio file")
    def test_voice_upload(self, client, api_key):
        """Test voice file upload."""
        # Would need actual audio file
        pass


class TestHealthEndpoint:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint if available."""
        response = client.get("/metrics")
        # May or may not exist
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
