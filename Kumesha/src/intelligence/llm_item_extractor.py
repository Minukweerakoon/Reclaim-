"""
LLM Item Extractor for AI-Driven Spatial-Temporal Validation
Extracts structured item information from natural language using LLMs.
Supports Gemini (primary) and Groq (fallback for rate limiting).
"""

import logging
import os
import json
from typing import Dict, Optional
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)


class LLMItemExtractor:
    """
    Extracts structured item information using LLMs.
    Uses Gemini as primary, Groq as fallback for rate limiting.
    """
    
    def __init__(self):
        """Initialize LLM clients with fallback support."""
        self.gemini_client = None
        self.groq_client = None
        self.cache: Dict[str, Dict] = {}
        self.use_groq_fallback = False
        
        # Initialize Gemini
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
                self.gemini_client = genai.GenerativeModel(model_name)
                logger.info(f"Initialized Gemini client: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
        
        # Initialize Groq fallback
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self.groq_client = Groq(api_key=api_key)
                self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
                logger.info(f"Initialized Groq fallback: {self.groq_model}")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq: {e}")
    
    def extract(self, text: str, use_cache: bool = True) -> Dict:
        """
        Extract item information from text.
        
        Args:
            text: Natural language description of the item
            use_cache: Whether to use cached results
        
        Returns:
            Dict with extracted information:
            {
                "item": "laptop",
                "category": "electronics",
                "specific_type": "MacBook Pro",
                "brand": "Apple",
                "attributes": ["portable", "valuable"],
                "confidence": 0.95
            }
        """
        # Check cache first
        cache_key = self._get_cache_key(text)
        if use_cache and cache_key in self.cache:
            logger.debug(f"Cache hit for '{text}'")
            return self.cache[cache_key]
        
        # Try Gemini first, then Groq fallback
        result = None
        if self.gemini_client and not self.use_groq_fallback:
            result = self._extract_with_gemini(text)
        
        # Fallback to Groq if Gemini fails or is rate limited
        if result is None and self.groq_client:
            logger.info("Falling back to Groq for item extraction")
            result = self._extract_with_groq(text)
            self.use_groq_fallback = True  # Temporarily prefer Groq
        
        # Default fallback if both fail
        if result is None:
            logger.error(f"Failed to extract item from '{text}' with all providers")
            result = self._get_default_extraction(text)
        
        # Cache result
        self.cache[cache_key] = result
        return result
    
    def _extract_with_gemini(self, text: str) -> Optional[Dict]:
        """Extract using Gemini API."""
        try:
            prompt = self._build_extraction_prompt(text)
            response = self.gemini_client.generate_content(prompt)
            
            # Reset fallback flag on success
            self.use_groq_fallback = False
            
            return self._parse_llm_response(response.text, text)
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "quota" in error_msg or "429" in error_msg:
                logger.warning(f"Gemini rate limited: {e}")
                return None  # Signal to use fallback
            else:
                logger.error(f"Gemini extraction error: {e}")
                return None
    
    def _extract_with_groq(self, text: str) -> Optional[Dict]:
        """Extract using Groq API."""
        try:
            prompt = self._build_extraction_prompt(text)
            
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured item information from text."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            return self._parse_llm_response(response.choices[0].message.content, text)
            
        except Exception as e:
            logger.error(f"Groq extraction error: {e}")
            return None
    
    def _build_extraction_prompt(self, text: str) -> str:
        """Build LLM prompt for item extraction."""
        return f"""Extract item information from the following text and return ONLY a valid JSON object.

Text: "{text}"

Return a JSON object with these fields:
- item: the general item type (e.g., "phone", "laptop", "backpack")
- category: broader category (e.g., "electronics", "bags", "accessories")
- specific_type: specific model/variant if mentioned (e.g., "MacBook Pro", "iPhone 15")
- brand: brand name if mentioned (or null)
- attributes: list of describing words (e.g., ["portable", "valuable", "work-related"])
- confidence: your confidence in the extraction (0.0-1.0)

Example output:
{{"item": "laptop", "category": "electronics", "specific_type": "MacBook Pro", "brand": "Apple", "attributes": ["portable", "valuable"], "confidence": 0.95}}

Return ONLY the JSON object, no other text."""
    
    def _parse_llm_response(self, response_text: str, original_text: str) -> Optional[Dict]:
        """Parse LLM response into structured format."""
        try:
            # Clean response - extract JSON if wrapped in markdown
            cleaned = response_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            result = json.loads(cleaned)
            
            # Validate required fields
            required_fields = ["item", "category"]
            if not all(field in result for field in required_fields):
                logger.warning(f"Missing required fields in LLM response")
                return None
            
            # Ensure defaults for optional fields
            result.setdefault("specific_type", None)
            result.setdefault("brand", None)
            result.setdefault("attributes", [])
            result.setdefault("confidence", 0.8)
            
            logger.debug(f"Extracted from '{original_text}': {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}\nResponse: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def _get_default_extraction(self, text: str) -> Dict:
        """Fallback extraction when LLM fails."""
        # Simple rule-based extraction as final fallback
        text_lower = text.lower()
        
        # Common item keywords
        item_map = {
            "phone": ["phone", "mobile", "iphone", "smartphone"],
            "laptop": ["laptop", "macbook", "notebook", "computer"],
            "bag": ["bag", "backpack", "purse", "handbag"],
            "wallet": ["wallet", "purse"],
            "keys": ["key", "keys"],
            "watch": ["watch", "smartwatch"],
            "headphones": ["headphone", "earbud", "airpod"],
        }
        
        detected_item = "unknown"
        for item, keywords in item_map.items():
            if any(kw in text_lower for kw in keywords):
                detected_item = item
                break
        
        return {
            "item": detected_item,
            "category": "unknown",
            "specific_type": None,
            "brand": None,
            "attributes": [],
            "confidence": 0.3  # Low confidence for fallback
        }
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear the extraction cache."""
        self.cache.clear()
        logger.info("Cleared LLM extraction cache")


# Global singleton
_llm_extractor = None


def get_llm_extractor() -> LLMItemExtractor:
    """Get or create the global LLM extractor instance."""
    global _llm_extractor
    if _llm_extractor is None:
        _llm_extractor = LLMItemExtractor()
    return _llm_extractor
