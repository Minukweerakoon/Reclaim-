"""
Feedback API Endpoint for Active Learning
Allows users to correct AI predictions and improve the system
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from src.intelligence.active_learning import get_active_learning_system
from src.api.auth import get_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

class FeedbackRequest(BaseModel):
    """User feedback submission"""
    input_text: str
    original_prediction: Dict
    user_correction: Dict
    feedback_type: str = "correction"

class FeedbackResponse(BaseModel):
    """Feedback confirmation"""
    status: str
    contribution_count: int
    message: str

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest, api_key: str = Depends(get_api_key)):
    """
    Submit user correction to improve the AI system.
    
    This powers our active learning feature - the system learns from user feedback!
    """
    try:
        active_learning = get_active_learning_system()
        
        # Record the feedback
        feedback_entry = active_learning.record_feedback(
            input_text=feedback.input_text,
            original_prediction=feedback.original_prediction,
            user_correction=feedback.user_correction,
            feedback_type=feedback.feedback_type
        )
        
        # Get total contributions
        contribution_count = active_learning.total_corrections
        
        return FeedbackResponse(
            status="recorded",
            contribution_count=contribution_count,
            message=f"Thank you! Your feedback helps improve the AI. Total contributions: {contribution_count}"
        )
        
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

@router.get("/stats")
async def get_feedback_stats(api_key: str = Depends(get_api_key)):
    """Get active learning statistics"""
    try:
        active_learning = get_active_learning_system()
        
        return {
            "total_corrections": active_learning.total_corrections,
            "buffer_size": len(active_learning.feedback_buffer),
            "max_buffer_size": 1000,
            "feature_status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        return {
            "total_corrections": 0,
            "buffer_size": 0,
            "feature_status": "unavailable",
            "error": str(e)
        }
