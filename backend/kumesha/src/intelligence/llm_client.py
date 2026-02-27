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
        
        # Initialize OpenAI client if using OpenAI
        if self.provider == "openai":
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.api_key)
                logger.info(f"✓ OpenAI client initialized with model: {self.model}")
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
                self.provider = "mock"
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
                self.provider = "mock"
        
        if self.provider == "gemini":
            if not _GENAI_AVAILABLE:
                logger.warning("Gemini provider requested but google.generativeai package not available. Falling back to mock.")
                self.provider = "mock"
            else:
                genai.configure(api_key=self.api_key)
                # Use model from env variable (expected: gemini-flash-latest)
                gemini_model_name = os.getenv("LLM_MODEL", "gemini-flash-latest")
                self.gemini_model = genai.GenerativeModel(gemini_model_name)
                self.gemini_fallback_model = genai.GenerativeModel("gemini-flash-latest")
                logger.info(f"✓ Loaded Gemini model: {gemini_model_name}")
            
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

    def guide_conversation(self, user_message: str, conversation_history: List[Dict] = None, previous_extracted_info: Dict = None) -> Dict:
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
            return self._gemini_guide_conversation(user_message, conversation_history, previous_extracted_info)
        elif self.provider == "openai":
            return self._openai_guide_conversation(user_message, conversation_history, previous_extracted_info)
        else:
            return self._mock_guide_conversation(user_message, conversation_history, previous_extracted_info)
    
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
        
        for attempt in range(self.retry_config["max_attempts"]):
            try:
                # The generative model name is accessible via `model.model_name` 
                # but we can safely just log that we are calling Gemini
                logger.info(f"Calling Gemini (attempt {attempt + 1}/{self.retry_config['max_attempts']})")
                
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
                    elif self.groq_client:
                        logger.warning("Gemini persistent error. Switching to Groq fallback...")
                        return self._call_groq_with_retry(prompt)
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
    
    def _gemini_guide_conversation(self, user_message: str, conversation_history: List[Dict] = None, previous_extracted_info: Dict = None) -> Dict:
        """Use Gemini to guide conversation intelligently."""
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in (conversation_history or [])
        ])
        
        # Format previously extracted info
        prev_info = previous_extracted_info or {}
        prev_info_text = "\n".join([
            f"  {k}: {v}" for k, v in prev_info.items() if v
        ])
        
        prompt = f"""You are a helpful assistant for a lost & found item reporting system.

Your tasks:
1. Detect if the user LOST an item or FOUND an item
   - Keywords for lost: lost, missing, can't find, dropped, left behind
   - Keywords for found: found, discovered, picked up, came across
   
2. Extract and ACCUMULATE details from the ENTIRE conversation:
   - Item type (phone, laptop, keys, wallet, bag, watch, shoes, jacket, etc.)
   - Color (red, blue, black, white, grey, silver, etc.)
   - Location (library, cafeteria, parking lot, gym, classroom, park, etc.)
   - Time (yesterday, today, this morning, 2pm, etc.)
   - Brand (Dell, Apple, Samsung, Nike, Adidas, Gucci, etc.)
   
   CRITICAL: Merge new information with previously extracted data. Keep all non-empty fields.
   
   EXAMPLES:
   - "I lost my blue Dell laptop" → item_type: "laptop", color: "blue", brand: "Dell"
   - "I lost my nike shoes yesterday at the park" → item_type: "shoes", color: "", brand: "Nike", location: "park", time: "yesterday"
   - "yesterday near the cafeteria" (when laptop already known) → keep laptop info, add time: "yesterday", location: "cafeteria"
   - "it was in the library" → location: "library"
   
3. Be empathetic and constructive:
   - Acknowledge what you've learned
   - Ask for missing details naturally (only ask for what's still missing)
   - Suggest validation when enough details collected
   
4. Guide next steps:
   - If all details collected → suggest validation
   - If missing critical info → ask for it

Previously extracted information:
{prev_info_text or '  (none yet)'}

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
            logger.info(f"Gemini raw response: {response_text[:200]}...")
            
            # Try to parse JSON
            result = json.loads(response_text)
            logger.info(f"Gemini extraction successful: {result.get('extracted_info', {})}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            logger.warning("Falling back to mock conversation handler")
            return self._mock_guide_conversation(user_message, conversation_history, previous_extracted_info)
        except Exception as e:
            logger.error(f"Gemini conversation error: {e}")
            logger.warning("Falling back to mock conversation handler")
            return self._mock_guide_conversation(user_message, conversation_history, previous_extracted_info)
    
    def _openai_guide_conversation(self, user_message: str, conversation_history: List[Dict] = None, previous_extracted_info: Dict = None) -> Dict:
        """Use OpenAI GPT-4 to guide conversation intelligently."""
        # Format previously extracted info
        prev_info = previous_extracted_info or {}
        prev_info_text = "\n".join([
            f"  {k}: {v}" for k, v in prev_info.items() if v
        ])
        
        # Build conversation messages for OpenAI
        messages = [
            {"role": "system", "content": """You are a helpful assistant for a lost & found item reporting system.

Extract and ACCUMULATE details from the ENTIRE conversation:
- Item type (phone, laptop, keys, wallet, bag, watch, etc.)
- Color (red, blue, black, white, grey, silver, etc.)
- Location (library, cafeteria, parking lot, gym, classroom, etc.)
- Time (yesterday, today, this morning, 2pm, etc.)
- Brand (Dell, Apple, Samsung, HP, etc.)

CRITICAL: Merge new information with previously extracted data. Keep all non-empty fields.

Detect if the user LOST or FOUND an item.

Respond ONLY with valid JSON in this exact format:
{
  "response": "Your friendly, conversational response",
  "intention": "lost" or "found" or "unknown",
  "extracted_info": {
    "item_type": "extracted item or empty string",
    "color": "extracted color or empty string",
    "location": "extracted location or empty string",
    "time": "extracted time or empty string",
    "brand": "extracted brand or empty string"
  },
  "next_action": "ask_for_image" or "ask_for_details" or "validate" or "continue",
  "sentiment": "sentimental" or "neutral" or "urgent"
}"""}
        ]
        
        # Add conversation history
        for msg in (conversation_history or []):
            messages.append({"role": "user" if msg["role"] == "user" else "assistant", "content": msg["content"]})
        
        # Add context about previously extracted info
        context = f"Previously extracted: {prev_info_text or 'none yet'}\nUser's latest message: {user_message}"
        messages.append({"role": "user", "content": context})
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"OpenAI raw response: {response_text[:200]}...")
            
            result = json.loads(response_text)
            logger.info(f"OpenAI extraction successful: {result.get('extracted_info', {})}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"OpenAI returned invalid JSON: {e}")
            logger.warning("Falling back to mock conversation handler")
            return self._mock_guide_conversation(user_message, conversation_history, previous_extracted_info)
        except Exception as e:
            logger.error(f"OpenAI conversation error: {e}")
            logger.warning("Falling back to mock conversation handler")
            return self._mock_guide_conversation(user_message, conversation_history, previous_extracted_info)
    
    def _mock_guide_conversation(self, user_message: str, conversation_history: List[Dict] = None, previous_extracted_info: Dict = None) -> Dict:
        """Mock conversation guidance for testing."""
        msg_lower = user_message.lower()
        
        # Check conversation history for previous intent
        previous_intent = "unknown"
        if conversation_history:
            for msg in reversed(conversation_history):
                content = msg.get('content', '').lower()
                if any(word in content for word in ['lost', 'missing', "can't find", 'dropped', 'lose']):
                    previous_intent = "lost"
                    break
                elif any(word in content for word in ['found', 'discovered', 'picked up', 'find']):
                    previous_intent = "found"
                    break
        
        # Detect intention from current message
        intention = "unknown"
        if any(word in msg_lower for word in ['lost', 'missing', "can't find", 'dropped', 'lose']):
            intention = "lost"
        elif any(word in msg_lower for word in ['found', 'discovered', 'picked up', 'find']):
            intention = "found"
        
        # Use previous intent if current message doesn't specify
        if intention == "unknown" and previous_intent != "unknown":
            intention = previous_intent
        
        # Start with previous extracted info or empty dict
        extracted = previous_extracted_info.copy() if previous_extracted_info else {
            "item_type": "",
            "color": "",
            "location": "",
            "time": "",
            "brand": ""
        }
        
        # Extract basic info from current message and merge
        # Item types
        item_mapping = {
            'phone': 'phone',
            'iphone': 'phone',
            'laptop': 'laptop',
            'macbook': 'laptop',
            'computer': 'laptop',
            'keys': 'keys',
            'wallet': 'wallet',
            'watch': 'watch',
            'bag': 'bag',
            'backpack': 'bag',
            'tablet': 'tablet',
            'ipad': 'tablet',
            'shoe': 'shoes',
            'shoes': 'shoes',
            'sneaker': 'shoes',
            'sneakers': 'shoes',
            'jacket': 'jacket',
            'coat': 'coat'
        }
        for kw, item in item_mapping.items():
            if kw in msg_lower:
                extracted["item_type"] = item
                break
        
        # Colors
        colors = ['red', 'blue', 'black', 'white', 'silver', 'gold', 'green', 'grey', 'gray']
        for color in colors:
            if color in msg_lower:
                extracted["color"] = color
                break
        
        # Locations
        locations = ['library', 'cafeteria', 'parking', 'classroom', 'gym', 'cafe', 'park', 'bus', 'train']
        for loc in locations:
            if loc in msg_lower:
                extracted["location"] = loc
                break
        
        # Time expressions
        time_keywords = ['yesterday', 'today', 'morning', 'afternoon', 'evening', 'ago', 'a.m', 'p.m', 'am', 'pm']
        if any(kw in msg_lower for kw in time_keywords):
            # Extract time-related text (simplified)
            time_words = [w for w in user_message.split() if any(kw in w.lower() for kw in time_keywords)]
            if time_words:
                extracted["time"] = " ".join(time_words)[:50]  # Limit length
        
        # Brands
        brand_mapping = {
            'dell': 'Dell',
            'hp': 'HP',
            'apple': 'Apple',
            'macbook': 'Apple',
            'iphone': 'Apple',
            'ipad': 'Apple',
            'samsung': 'Samsung',
            'lenovo': 'Lenovo',
            'asus': 'Asus',
            'acer': 'Acer',
            'nike': 'Nike',
            'adidas': 'Adidas',
            'puma': 'Puma',
            'gucci': 'Gucci',
            'louis vuitton': 'Louis Vuitton'
        }
        for kw, brand in brand_mapping.items():
            if kw in msg_lower:
                extracted["brand"] = brand
                break
        
        # Generate response
        if intention == "lost":
            if extracted["item_type"]:
                response = f"I understand you lost your {extracted['item_type']}. "
                
                # Check what's missing
                missing = []
                if not extracted["location"]: missing.append("where you last saw it")
                if not extracted["time"]: missing.append("when you lost it")
                if not extracted["color"]: missing.append("its color")
                
                if not missing:
                    response += "I've noted all the details. Would you like to proceed to validation to search for matches?"
                else:
                    response += f"Could you tell me {', '.join(missing)}?"
            else:
                response = "I'm sorry to hear that. What specifically did you lose?"
                
        elif intention == "found":
            if extracted["item_type"]:
                response = f"Thank you for reporting this. I've noted the {extracted['item_type']}. "
                if not extracted["location"]:
                    response += "Where exactly did you find it?"
                else:
                    response += "Would you like to take a photo or provide more details to help the owner find it?"
            else:
                response = "Thank you for reporting a found item. What specifically did you find?"
        else:
            # Only show initial greeting if this is actually the start of conversation
            if not conversation_history or len(conversation_history) <= 1:
                response = "Hi! I'm here to help. Did you lose something or find something?"
            else:
                # Continue conversation even if intent is unclear
                response = "I see. Can you tell me more about what happened? What item are we talking about?"
        
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
