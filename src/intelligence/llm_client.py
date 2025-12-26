import os
import logging
from typing import Dict, Optional, List
import json
from dotenv import load_dotenv

# Load environment variables (safe to call multiple times)
load_dotenv()

logger = logging.getLogger(__name__)

import google.generativeai as genai

class LLMClient:
    """
    Unified client for interacting with Large Language Models.
    Supports: Mock (default), OpenAI, Gemini.
    Enhanced with conversational guidance for lost & found items.
    """
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "mock").lower()
        self.api_key = os.getenv("OPENAI_API_KEY") if self.provider == "openai" else os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo")
        
        if self.provider != "mock" and not self.api_key:
            logger.warning(f"No API key found for {self.provider}. Falling back to mock provider.")
            self.provider = "mock"
        
        if self.provider == "gemini":
            genai.configure(api_key=self.api_key)
            # Using gemini-2.5-flash (confirmed available via list_models())
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            
        # DEBUG LOGGING
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if self.api_key else "None"
        print(f"DEBUG: LLMClient Initialized. Provider: {self.provider}, Key: {masked_key}")
        logger.info(f"LLMClient Initialized. Provider: {self.provider}, Key: {masked_key}")

    def guide_conversation(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        NEW: Guide user through item reporting with intelligent conversation.
        
        Uses Gemini to:
        1. Detect if user lost or found an item
        2. Extract relevant details (item, color, location, etc.)
        3. Ask constructive follow-up questions
        4. Show empathy for sentimental items
        
        Args:
            user_message: Latest message from user
            conversation_history: Previous messages for context
            
        Returns:
            {
                "response": "Bot's conversational response",
                "intention": "lost" | "found" | "unknown",
                "extracted_info": {
                    "item_type": str,
                    "color": str,
                    "location": str,
                    "time": str,
                    "brand": str
                },
                "next_action": "ask_for_image" | "ask_for_details" | "validate" | "continue",
                "sentiment": "sentimental" | "neutral" | "urgent"
            }
        """
        if self.provider == "gemini":
            return self._gemini_guide_conversation(user_message, conversation_history)
        else:
            return self._mock_guide_conversation(user_message, conversation_history)
    
    def _gemini_guide_conversation(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """Use Gemini to guide conversation intelligently."""
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in (conversation_history or [])
        ])
        
        prompt = f"""You are a helpful assistant for a lost & found item reporting system.

Your tasks:
1. Detect if the user LOST an item or FOUND an item
   - Keywords for lost: lost, missing, can't find, dropped, left behind
   - Keywords for found: found, discovered, picked up, came across
   
2. Extract details:
   - Item type (phone, laptop, keys, wallet, etc.)
   - Color
   - Location (library, cafeteria, parking lot, etc.)
   - Time (yesterday, this morning, 2 hours ago, etc.)
   - Brand (if mentioned)
   
3. Be empathetic and constructive:
   - If item has sentimental value, acknowledge it
   - Ask for missing details naturally
   - Suggest adding photo if user found an item
   - Suggest adding voice description for details
   
4. Guide next steps:
   - If all details collected → suggest validation
   - If missing image → suggest taking photo
   - If vague description → ask for more details

Conversation history:
{history_text}

User's latest message: {user_message}

Respond in JSON format:
{{
  "response": "Your friendly, conversational response to the user",
  "intention": "lost" or "found" or "unknown",
  "extracted_info": {{
    "item_type": "extracted item or empty string",
    "color": "extracted color or empty string",
    "location": "extracted location or empty string",
    "time": "extracted time or empty string",
    "brand": "extracted brand or empty string"
  }},
  "next_action": "ask_for_image" or "ask_for_details" or "validate" or "continue",
  "sentiment": "sentimental" or "neutral" or "urgent"
}}
"""
        
        try:
            # Configure generation to prefer JSON output
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Parse the JSON response
            response_text = response.text.strip()
            logger.info(f"Gemini raw response: {response_text[:200]}...")  # Log first 200 chars
            
            # Try to parse JSON
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            logger.error(f"Response was: {response.text[:500]}")
            return self._mock_guide_conversation(user_message, conversation_history)
        except Exception as e:
            logger.error(f"Gemini conversation error: {e}")
            return self._mock_guide_conversation(user_message, conversation_history)
    
    def _mock_guide_conversation(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """Mock conversation guidance for testing."""
        msg_lower = user_message.lower()
        
        # Detect intention
        intention = "unknown"
        if any(word in msg_lower for word in ['lost', 'missing', "can't find", 'dropped']):
            intention = "lost"
        elif any(word in msg_lower for word in ['found', 'discovered', 'picked up']):
            intention = "found"
        
        # Extract basic info
        extracted = {
            "item_type": "",
            "color": "",
            "location": "",
            "time": "",
            "brand": ""
        }
        
        # Item types
        items = ['phone', 'laptop', 'keys', 'wallet', 'watch', 'bag', 'backpack']
        for item in items:
            if item in msg_lower:
                extracted["item_type"] = item
                break
        
        # Colors
        colors = ['red', 'blue', 'black', 'white', 'silver', 'gold', 'green']
        for color in colors:
            if color in msg_lower:
                extracted["color"] = color
                break
        
        # Locations
        locations = ['library', 'cafeteria', 'parking', 'classroom', 'gym']
        for loc in locations:
            if loc in msg_lower:
                extracted["location"] = loc
                break
        
        # Generate response
        if intention == "lost":
            response = f"I understand you lost something. "
            if extracted["item_type"]:
                response += f"A {extracted['color']} {extracted['item_type']}" if extracted["color"] else f"a {extracted['item_type']}"
                response += f" in the {extracted['location']}" if extracted["location"] else ""
                response += ". Could you provide more details like when you last saw it?"
            else:
                response += "What did you lose?"
                
        elif intention == "found":
            response = f"Great! You found something. "
            if extracted["item_type"]:
                response += f"A {extracted['color']} {extracted['item_type']}" if extracted["color"] else f"a {extracted['item_type']}"
                response += ". Would you like to take a photo to help match it with the owner?"
            else:
                response += "What did you find?"
        else:
            response = "Hi! I'm here to help. Did you lose something or find something?"
        
        # Determine next action
        next_action = "continue"
        if extracted["item_type"] and extracted["location"]:
            if intention == "found":
                next_action = "ask_for_image"
            else:
                next_action = "ask_for_details"
        
        return {
            "response": response,
            "intention": intention,
            "extracted_info": extracted,
            "next_action": next_action,
            "sentiment": "neutral"
        }

    def analyze_text(self, text: str, context: Optional[Dict] = None) -> Dict:
        """
        Analyze text using the configured LLM provider.
        
        Args:
            text: The text to analyze
            context: Optional context (e.g., item category, previous messages)
            
        Returns:
            Dict containing analysis results (sentiment, entities, reasoning)
        """
        if self.provider == "mock":
            return self._mock_analysis(text)
        elif self.provider == "openai":
            return self._openai_analysis(text)
        elif self.provider == "gemini":
            return self._gemini_analysis(text)
        else:
            logger.error(f"Unknown provider: {self.provider}")
            return self._mock_analysis(text)

    def _mock_analysis(self, text: str) -> Dict:
        """
        Simulate LLM analysis for demonstration and testing.
        """
        text_lower = text.lower()
        
        # Scenario 1: Sentimental Value
        if any(w in text_lower for w in ["grandmother", "grandfather", "late", "gift from", "heirloom"]):
            return {
                "sentiment": "high_emotional_value",
               "reasoning": "The user mentioned a family connection ('grandmother', 'late'), indicating high sentimental value.",
                "clarification_needed": False,
                "entities": ["heirloom"]
            }
            
        # Scenario 2: Ambiguous Item
        if "ring" in text_lower and "diamond" in text_lower and "certificate" not in text_lower:
            return {
                "sentiment": "high_monetary_value",
                "reasoning": "High-value item detected ('Diamond Ring'). Missing authentication details.",
                "clarification_needed": True,
                "clarification_question": "For high-value items like diamond rings, do you have a GIA certificate number or a photo of the hallmark?",
                "entities": ["jewelry"]
            }
            
        # Default
        return {
            "sentiment": "neutral",
            "reasoning": "Standard item description.",
            "clarification_needed": False,
            "entities": []
        }

    def _openai_analysis(self, text: str) -> Dict:
        # Placeholder for OpenAI implementation
        return {"error": "OpenAI provider not fully implemented yet"}

    def _gemini_analysis(self, text: str) -> Dict:
        """
        Analyze text using Google Gemini API.
        """
        try:
            prompt = f"""Analyze this lost/found item description:

Text: {text}

Provide analysis in JSON format:
{{
  "sentiment": "high_emotional_value" or "neutral" or "high_monetary_value",
  "reasoning": "explanation of why you classified it this way",
  "clarification_needed": true or false,
  "clarification_question": "question to ask user if clarification needed, empty string otherwise",
  "entities": ["list", "of", "extracted", "entities"]
}}
"""
            response = self.gemini_model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return self._mock_analysis(text)

# Singleton instance
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
