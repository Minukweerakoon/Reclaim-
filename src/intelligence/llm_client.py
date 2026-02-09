import os
import logging
from typing import Dict, Optional, List
import json
from dotenv import load_dotenv

# Load environment variables (safe to call multiple times)
load_dotenv()

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"Failed to import google.generativeai: {e}")
    _GENAI_AVAILABLE = False
    genai = None

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
        
        # Groq fallback configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.groq_client = None
        
        # Retry configuration for rate limit handling
        self.retry_config = {
            "max_attempts": 3,
            "backoff_factor": 2,  # Exponential backoff: 1s, 2s, 4s
            "timeout": 10
        }
        
        if self.provider != "mock" and not self.api_key:
            logger.warning(f"No API key found for {self.provider}. Falling back to mock provider.")
            self.provider = "mock"
        
        if self.provider == "gemini":
            if not _GENAI_AVAILABLE:
                logger.warning("Gemini provider requested but google.generativeai package not available. Falling back to mock.")
                self.provider = "mock"
            else:
                genai.configure(api_key=self.api_key)
                # Using gemini-2.5-flash (confirmed available via list_models())
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Initialize Groq as fallback if API key available
            if self.groq_api_key:
                try:
                    from groq import Groq
                    self.groq_client = Groq(api_key=self.groq_api_key)
                    logger.info("Groq fallback initialized successfully")
                except ImportError:
                    logger.warning("Groq package not installed. Install with: pip install groq")
                except Exception as e:
                    logger.warning(f"Failed to initialize Groq fallback: {e}")
            else:
                logger.warning("No GROQ_API_KEY found. Groq fallback unavailable.")
            
        # DEBUG LOGGING
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if self.api_key else "None"
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
    
    def _call_gemini_with_retry(self, prompt: str, use_fallback: bool = False) -> str:
        """
        Call Gemini API with retry logic and exponential backoff.
        
        Args:
            prompt: The prompt to send
            use_fallback: If True, use fallback model (gemini-1.5-flash)
            
        Returns:
            Response text from Gemini
            
        Raises:
            Exception: If all retries fail
        """
        import time
        
        model = self.gemini_fallback_model if use_fallback else self.gemini_model
        model_name = "gemini-1.5-flash" if use_fallback else "gemini-2.5-flash"
        
        for attempt in range(self.retry_config["max_attempts"]):
            try:
                logger.info(f"Calling {model_name} (attempt {attempt + 1}/{self.retry_config['max_attempts']})")
                
                # Add timeout to prevent indefinite hangs
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json"
                    ),
                    request_options={"timeout": 30}  # 30 second timeout
                )
                
                return response.text.strip()
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                    if attempt < self.retry_config["max_attempts"] - 1:
                        # Exponential backoff
                        wait_time = self.retry_config["backoff_factor"] ** attempt
                        logger.warning(f"Rate limit hit. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    elif self.groq_client:
                        # Try Groq fallback instead of non-existent gemini-1.5-flash
                        logger.warning("Gemini rate limited. Switching to Groq fallback...")
                        return self._call_groq_with_retry(prompt)
                    else:
                        # No fallback available
                        logger.error("Gemini rate limited and no Groq fallback available")
                        raise
                else:
                    # Non-rate-limit error, log and retry
                    logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                    if attempt < self.retry_config["max_attempts"] - 1:
                        time.sleep(1)  # Brief pause before retry
                        continue
                    else:
                        raise
        
        raise Exception("All retry attempts failed")
    
    def _call_groq_with_retry(self, prompt: str) -> str:
        """
        Call Groq API with retry logic.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Response text from Groq
            
        Raises:
            Exception: If all retries fail
        """
        import time
        import json
        
        for attempt in range(self.retry_config["max_attempts"]):
            try:
                logger.info(f"Calling Groq {self.groq_model} (attempt {attempt + 1}/{self.retry_config['max_attempts']})")
                
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    timeout=30
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"Groq API error (attempt {attempt + 1}): {e}")
                
                if attempt < self.retry_config["max_attempts"] - 1:
                    wait_time = self.retry_config["backoff_factor"] ** attempt
                    logger.warning(f"Groq error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        raise Exception("All Groq retry attempts failed")
    
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
            # Use retry wrapper for robust API calls
            response_text = self._call_gemini_with_retry(prompt)
            
            # Parse the JSON response
            logger.info(f"Gemini raw response: {response_text[:200]}...")  # Log first 200 chars
            
            # Try to parse JSON
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            logger.error(f"Response was: {response_text[:500]}")
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
