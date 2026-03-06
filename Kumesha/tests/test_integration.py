





















import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import os

class TestIntegrationScenarios:
    """
    Comprehensive integration tests covering real-world scenarios.
    """
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        from src.api.main import app
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_high_quality_multimodal_submission(self, client):
        """
        Test scenario: User submits high-quality inputs across all modalities.
        Expected: All validations pass, high confidence score, forward to matching.
        """
        # Prepare test data
        image_path = "tests/fixtures/clear_red_iphone.jpg"
        text = "Lost my red iPhone 13 in the library yesterday afternoon"
        audio_path = "tests/fixtures/clear_voice_description.wav"
        
        with open(image_path, 'rb') as img, open(audio_path, 'rb') as audio:
            response = await client.post(
                "/validate/complete",
                data={"text": text},
                files={
                    "image_file": ("image.jpg", img, "image/jpeg"),
                    "audio_file": ("voice.wav", audio, "audio/wav")
                },
                headers={"X-API-Key": "test-api-key"}
            )
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate response structure
        assert "image" in result
        assert "text" in result
        assert "voice" in result
        assert "cross_modal" in result
        assert "confidence" in result
        
        # Validate individual components
        assert result["image"]["valid"] == True
        assert result["text"]["valid"] == True
        assert result["voice"]["valid"] == True
        
        # Validate cross-modal consistency
        assert result["cross_modal"]["image_text"]["valid"] == True
        assert result["cross_modal"]["voice_text"]["valid"] == True
        
        # Validate routing decision
        assert result["confidence"]["overall_confidence"] >= 0.85
        assert result["confidence"]["routing"] == "high_quality"
        assert result["confidence"]["action"] == "forward_to_matching"
    
    @pytest.mark.asyncio
    async def test_mismatch_detection_scenario(self, client):
        """
        Test the documented mismatch scenario:
        - Image: Red iPhone
        - Text: Blue Samsung
        - Voice: Black phone at cafeteria
        
        Expected: Mismatches detected, low confidence, return for improvement
        """
        image_path = "tests/fixtures/red_iphone.jpg"
        text = "Lost my blue Samsung Galaxy S22 near the library yesterday"
        audio_path = "tests/fixtures/black_phone_cafeteria.wav"
        
        with open(image_path, 'rb') as img, open(audio_path, 'rb') as audio:
            response = await client.post(
                "/validate/complete",
                data={"text": text},
                files={
                    "image_file": ("image.jpg", img, "image/jpeg"),
                    "audio_file": ("voice.wav", audio, "audio/wav")
                },
                headers={"X-API-Key": "test-api-key"}
            )
        
        assert response.status_code == 200
        result = response.json()
        
        # Validate mismatches detected
        assert result["cross_modal"]["image_text"]["valid"] == False
        assert result["cross_modal"]["image_text"]["similarity"] < 0.85
        
        assert result["cross_modal"]["voice_text"]["valid"] == False
        
        # Validate low confidence and rejection
        assert result["confidence"]["overall_confidence"] < 0.70
        assert result["confidence"]["routing"] == "low_quality"
        assert result["confidence"]["action"] == "return_for_improvement"
        
        # Validate specific feedback
        feedback = result["feedback"]
        assert any("image" in suggestion and "Samsung" in suggestion 
                  for suggestion in feedback["suggestions"])
        assert any("color" in suggestion for suggestion in feedback["suggestions"])
    
    @pytest.mark.asyncio
    async def test_performance_requirement_3_seconds(self, client):
        """
        Test that complete validation completes within 3 seconds.
        """
        import time
        
        image_path = "tests/fixtures/test_image.jpg"
        text = "Lost my laptop in the cafeteria"
        
        start_time = time.time()
        
        with open(image_path, 'rb') as img:
            response = await client.post(
                "/validate/complete",
                data={"text": text},
                files={"image_file": ("image.jpg", img, "image/jpeg")},
                headers={"X-API-Key": "test-api-key"}
            )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        assert processing_time < 3.0, f"Processing took {processing_time}s (target: <3s)"
    
    @pytest.mark.asyncio
    async def test_concurrent_load_100_requests(self, client):
        """
        Test system can handle 100 concurrent requests.
        """
        async def make_request():
            response = await client.post(
                "/validate/text",
                json={"text": "Lost my red phone in library", "language": "en"},
                headers={"X-API-Key": "test-api-key"}
            )
            return response.status_code == 200
        
        # Create 100 concurrent requests
        tasks = [make_request() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.95, f"Success rate: {success_rate*100}% (target: 95%+)"
