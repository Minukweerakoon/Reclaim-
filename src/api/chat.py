"""
Chat API Endpoint for Conversational Lost & Found Reporting
Integrates Gem

ini-guided conversation into the chatbot
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.intelligence.llm_client import get_llm_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str  # "user" or "bot"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    bot_response: str
    intention: str  # "lost", "found", or "unknown"
    extracted_info: Dict
    next_action: str
    sentiment: str

@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """
    Gemini-powered conversational guidance for lost & found reporting.
    
    Features:
    - Auto-detects if user lost or found an item
    - Extracts item details intelligently
    - Provides constructive feedback
    - Shows empathy for sentimental items
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
        
        return ChatResponse(
            bot_response=response["response"],
            intention=response["intention"],
            extracted_info=response["extracted_info"],
            next_action=response["next_action"],
            sentiment=response["sentiment"]
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
