"""
Tests for Active Learning Feedback Loop
"""
import pytest
from fastapi.testclient import TestClient
from app import app
from src.database.db import DatabaseManager
from datetime import datetime

client = TestClient(app)
API_KEY = "test_api_key_12345" # Matches config

def test_submit_feedback_success():
    """Test successful feedback submission."""
    payload = {
        "request_id": "test_req_123",
        "modality": "image",
        "predicted_label": "phone",
        "user_correction": "remote",
        "is_correct": False,
        "comments": "Visually similar but buttons are different"
    }
    
    response = client.post(
        "/feedback",
        json=payload,
        headers={"X-API-Key": API_KEY}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["active_learning_triggered"] == True

def test_submit_positive_feedback():
    """Test positive feedback (correct prediction)."""
    payload = {
        "request_id": "test_req_456",
        "modality": "text",
        "predicted_label": "wallet",
        "is_correct": True
    }
    
    response = client.post(
        "/feedback",
        json=payload,
        headers={"X-API-Key": API_KEY}
    )
    
    assert response.status_code == 200
    assert response.json()["active_learning_triggered"] == False

def test_feedback_unauthorized():
    """Test feedback without API key."""
    response = client.post(
        "/feedback",
        json={}
    )
    assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
