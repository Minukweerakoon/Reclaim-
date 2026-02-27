import pytest
from unittest.mock import patch, MagicMock
from src.integration.external_service import ExternalIntegrationService

# Mock data
MOCK_VALIDATION_DATA = {
    "request_id": "test-uuid-123",
    "timestamp": "2025-01-01T12:00:00",
    "input_types": ["image", "text"],
    "confidence": {
        "overall_confidence": 0.95,
        "action": "forward_to_matching"
    },
    "text": "A red nike shoe",
    "image": {"valid": True},
    "voice": None
}

class TestExternalIntegration:
    
    @patch('src.integration.external_service.requests.post')
    def test_post_validated_item_success(self, mock_post):
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "ext-123"}
        mock_post.return_value = mock_response
        
        # Initialize service (it reads env vars, so we default to enabled)
        service = ExternalIntegrationService()
        service.enabled = True
        service.service_url = "http://test-server/api"
        
        # Execute
        result = service.post_validated_item(MOCK_VALIDATION_DATA, image_path=None)
        
        # Verify
        assert result["status"] == "success"
        assert result["external_id"] == "ext-123"
        mock_post.assert_called_once()
        
        # Verify payload structure
        args, kwargs = mock_post.call_args
        payload = kwargs['data']
        assert payload['confidence_score'] == 0.95
        assert payload['validation_action'] == "forward_to_matching"

    @patch('src.integration.external_service.requests.post')
    def test_post_validated_item_failure(self, mock_post):
        # Setup mock to fail
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        service = ExternalIntegrationService()
        service.enabled = True
        
        result = service.post_validated_item(MOCK_VALIDATION_DATA)
        
        assert result["status"] == "failed"
        assert "Connection refused" in result["error"]
