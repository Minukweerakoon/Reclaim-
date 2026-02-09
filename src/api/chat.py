"""
Chat API Endpoint for Conversational Lost & Found Reporting
Integrates Gemini-guided conversation into the chatbot
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.intelligence.llm_client import get_llm_client
from src.intelligence.active_learning import get_active_learning_system
from src.api.auth import get_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str  # "user" or "bot"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    previous_prediction: Optional[Dict] = None  # For tracking corrections

class ChatResponse(BaseModel):
    bot_response: str
    intention: str  # "lost", "found", or "unknown"
    extracted_info: Dict
    next_action: str
    sentiment: str
    feedback_recorded: bool = False  # Indicates if active learning captured this

@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest, api_key: str = Depends(get_api_key)):
    """
    Gemini-powered conversational guidance for lost & found reporting.
    
    Features:
    - Auto-detects if user lost or found an item
    - Extracts item details intelligently
    - Provides constructive feedback
    - Shows empathy for sentimental items
    - Records corrections for active learning (Novel Feature #2)
    """
    try:
        llm_client = get_llm_client()
        
        # Convert history to dict format
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        # Get conversational response from Gemini
        response = llm_client.guide_conversation(
            user_message=request.message,
            conversation_history=history
        )
        
        feedback_recorded = False
        
        # Check if this is a correction (user correcting a previous prediction)
        correction_keywords = ['actually', 'no,', 'not', 'wrong', "it's a", "it is a", 'correction:', 'sorry']
        is_correction = any(kw.lower() in request.message.lower() for kw in correction_keywords)
        
        if is_correction and request.previous_prediction:
            try:
                active_learning = get_active_learning_system()
                active_learning.record_feedback(
                    input_text=request.message,
                    original_prediction=request.previous_prediction,
                    user_correction=response.get("extracted_info", {}),
                    feedback_type="correction"
                )
                feedback_recorded = True
                logger.info(f"Active learning: Recorded correction feedback for '{request.message}'")
            except Exception as e:
                logger.warning(f"Failed to record active learning feedback: {e}")
        
        # Also record feedback if Gemini detected the user is clarifying/correcting
        if response.get("sentiment") == "clarifying" or response.get("next_action") == "confirm_correction":
            try:
                active_learning = get_active_learning_system()
                active_learning.record_feedback(
                    input_text=request.message,
                    original_prediction=request.previous_prediction or {},
                    user_correction=response.get("extracted_info", {}),
                    feedback_type="clarification"
                )
                feedback_recorded = True
                logger.info(f"Active learning: Recorded clarification from '{request.message}'")
            except Exception as e:
                logger.warning(f"Failed to record active learning feedback: {e}")
        
        return ChatResponse(
            bot_response=response["response"],
            intention=response["intention"],
            extracted_info=response["extracted_info"],
            next_action=response["next_action"],
            sentiment=response["sentiment"],
            feedback_recorded=feedback_recorded
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

