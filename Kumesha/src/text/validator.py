import os
import re
import time
import logging
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, List, Optional, Any, Union, Tuple
import spacy
from spacy.cli import download as spacy_download
import numpy as np
import torch
from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
from src.intelligence.llm_client import get_llm_client
from src.intelligence.knowledge_graph import get_knowledge_graph
from src.intelligence.active_learning import get_active_learning_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TextValidator:
    """An intelligent text validation system for lost item descriptions using NLP techniques.
    
    This class provides methods to validate text descriptions based on various criteria:
    - Completeness analysis (item type, color, location)
    - Semantic coherence validation using BERT embeddings
    - Entity extraction using spaCy NER
    - Feedback generation for incomplete descriptions
    
    The validation pipeline returns structured results in JSON format.
    """
    
    # Supported languages
    SUPPORTED_LANGUAGES = ['en', 'si', 'ta']
    
    # Maximum text length in characters
    MAX_TEXT_LENGTH = 1000
    
    # Default item types dictionary (can be extended)
    DEFAULT_ITEM_TYPES = {
        'en': ['phone', 'wallet', 'keys', 'bag', 'backpack', 'laptop', 'umbrella', 'watch', 'glasses', 'headphones', 'camera', 'book', 'jacket', 'purse', 'card', 'shoes', 'shirt', 'clothing'],
        'si': ['දුරකථනය', 'පසුම්බිය', 'යතුරු', 'බෑගය', 'පිටිපසුම්බිය', 'ලැප්ටොප්', 'කුඩය', 'ඔරලෝසුව', 'කණ්ණාඩි', 'හෙඩ්ෆෝන්', 'කැමරාව', 'පොත', 'ජැකට්', 'පර්ස්', 'කාඩ්පත', 'සපත්තු', 'කමිසය', 'ඇඳුම්'],
        'ta': ['தொலைபேசி', 'பணப்பை', 'சாவிகள்', 'பை', 'பின்புறப்பை', 'மடிக்கணினி', 'குடை', 'கடிகாரம்', 'கண்ணாடி', 'தலைப்பொறி', 'புகைப்படக்கருவி', 'புத்தகம்', 'ஜாக்கெட்', 'பணப்பை', 'அட்டை', 'காலணிகள்', 'சட்டை', 'ஆடைகள்']
    }
    
    # Default colors dictionary (can be extended)
    DEFAULT_COLORS = {
        'en': ['black', 'white', 'red', 'blue', 'green', 'yellow', 'brown', 'gray', 'purple', 'orange', 'pink', 'silver', 'gold'],
        'si': ['කළු', 'සුදු', 'රතු', 'නිල්', 'කොළ', 'කහ', 'දුඹුරු', 'අළු', 'දම්', 'තැඹිලි', 'රෝස', 'රිදී', 'රන්'],
        'ta': ['கருப்பு', 'வெள்ளை', 'சிவப்பு', 'நீலம்', 'பச்சை', 'மஞ்சள்', 'பழுப்பு', 'சாம்பல்', 'ஊதா', 'ஆரஞ்சு', 'இளஞ்சிவப்பு', 'வெள்ளி', 'தங்கம்']
    }
    
    # Default location terms — actual place names, NOT prepositions
    DEFAULT_LOCATIONS = {
        'en': [
            'library', 'cafeteria', 'canteen', 'classroom', 'parking', 'gym',
            'office', 'hallway', 'gate', 'station', 'building', 'lab',
            'laboratory', 'auditorium', 'corridor', 'lobby', 'entrance',
            'exit', 'restroom', 'bathroom', 'toilet', 'reception', 'park',
            'playground', 'field', 'yard', 'movie theater', 'theater',
            'cinema', 'mall', 'store', 'shop', 'restaurant', 'cafe',
            'bus stop', 'train station', 'airport', 'hospital', 'hotel',
            'church', 'museum', 'stadium', 'beach', 'market', 'supermarket',
            'bank', 'bar', 'club', 'university', 'school', 'college',
            'campus', 'dorm', 'dormitory', 'apartment', 'house', 'street',
            'road', 'bus', 'train', 'taxi', 'subway', 'metro', 'study area'
        ],
        'si': [],
        'ta': []
    }
    
    DEFAULT_BRANDS = {
        'en': [
            'gucci', 'louis vuitton', 'prada', 'apple', 'samsung', 'lenovo',
            'dell', 'hp', 'nike', 'adidas', 'coach', 'hermes', 'fossil',
            'michael kors', 'lacoste', 'beats'
        ],
        'si': [],
        'ta': []
    }
    
    def __init__(self, 
                 item_types: Optional[Dict[str, List[str]]] = None,
                 colors: Optional[Dict[str, List[str]]] = None,
                 locations: Optional[Dict[str, List[str]]] = None,
                 completeness_threshold: float = 0.7,
                 coherence_threshold: float = 0.6,
                 bert_model_name: str = 'bert-base-multilingual-cased',
                 sentence_transformer_model: str = 'paraphrase-multilingual-mpnet-base-v2',
                 enable_logging: bool = True):
        """Initialize the TextValidator with configurable parameters.
        
        Args:
            item_types: Dictionary of item type keywords by language (default: None, uses DEFAULT_ITEM_TYPES)
            colors: Dictionary of color keywords by language (default: None, uses DEFAULT_COLORS)
            locations: Dictionary of location terms by language (default: None, uses DEFAULT_LOCATIONS)
            completeness_threshold: Threshold for completeness score (default: 0.7)
            coherence_threshold: Threshold for semantic coherence score (default: 0.6)
            bert_model_name: Name of the BERT model to use (default: 'bert-base-multilingual-cased')
            sentence_transformer_model: Name of the sentence transformer model (default: 'paraphrase-multilingual-mpnet-base-v2')
            enable_logging: Whether to enable logging (default: True)
        """
        self.item_types = item_types if item_types is not None else self.DEFAULT_ITEM_TYPES
        self.colors = colors if colors is not None else self.DEFAULT_COLORS
        self.locations = locations if locations is not None else self.DEFAULT_LOCATIONS
        self.brands = self.DEFAULT_BRANDS
        self.completeness_threshold = completeness_threshold
        self.coherence_threshold = coherence_threshold
        self.enable_logging = enable_logging

        # Sanitize multilingual keyword lists if encoding is corrupted
        try:
            def _has_non_ascii(tokens: List[str]) -> bool:
                return any(any(ord(ch) > 127 for ch in t) for t in tokens)

            for lang in ['si', 'ta']:
                if lang in self.item_types and _has_non_ascii(self.item_types.get(lang, [])):
                    self.item_types[lang] = self.item_types.get('en', [])
                if lang in self.colors and _has_non_ascii(self.colors.get(lang, [])):
                    self.colors[lang] = self.colors.get('en', [])
                if lang in self.locations and _has_non_ascii(self.locations.get(lang, [])):
                    self.locations[lang] = self.locations.get('en', [])
                if lang in self.brands and _has_non_ascii(self.brands.get(lang, [])):
                    self.brands[lang] = self.brands.get('en', [])
        except Exception:
            # On any issue, fall back to English lists for all languages
            self.item_types['si'] = self.item_types.get('en', [])
            self.item_types['ta'] = self.item_types.get('en', [])
            self.colors['si'] = self.colors.get('en', [])
            self.colors['ta'] = self.colors.get('en', [])
            self.locations['si'] = self.locations.get('en', [])
            self.locations['ta'] = self.locations.get('en', [])
            self.brands['si'] = self.brands.get('en', [])
            self.brands['ta'] = self.brands.get('en', [])

            # Also update the class-level keyword maps if they are used as fallbacks
            # (Though in this implementation, the class attributes are separate from instance attributes)

        # Initialize LLM Client (optional - don't fail if unavailable)
        try:
            self.llm_client = get_llm_client()
            if self.enable_logging:
                logger.info("LLM Client initialized")
        except Exception as e:
            if self.enable_logging:
                logger.warning(f"LLM Client unavailable: {e}")
            self.llm_client = None
        
        # Initialize Knowledge Graph (Research-Grade Feature #1) - optional
        try:
            self.knowledge_graph = get_knowledge_graph()
            if self.enable_logging:
                logger.info("Knowledge Graph initialized for context-aware validation")
        except Exception as e:
            if self.enable_logging:
                logger.warning(f"Knowledge Graph unavailable: {e}")
            self.knowledge_graph = None
        
        # Initialize Active Learning System (Research-Grade Feature #2) - optional
        try:
            self.active_learning = get_active_learning_system()
            if self.enable_logging:
                logger.info("Active Learning System initialized for self-improvement")
        except Exception as e:
            if self.enable_logging:
                logger.warning(f"Active Learning unavailable: {e}")
            self.active_learning = None

        # Ensure no corrupted multilingual keyword lists leak into runtime
        # Prefer empty lists over unreliable matches; production should load UTF-8 resources
        for lang in ['si', 'ta']:
            if not isinstance(self.item_types.get(lang, []), list):
                self.item_types[lang] = []
            if not isinstance(self.colors.get(lang, []), list):
                self.colors[lang] = []
            if not isinstance(self.locations.get(lang, []), list):
                self.locations[lang] = []
            if not isinstance(self.brands.get(lang, []), list):
                self.brands[lang] = []
        try:
            def _contains_non_ascii(seq: List[str]) -> bool:
                return any(any(ord(ch) > 127 for ch in token) for token in seq)
            for lang in ['si', 'ta']:
                if _contains_non_ascii(self.item_types.get(lang, [])):
                    self.item_types[lang] = []
                if _contains_non_ascii(self.colors.get(lang, [])):
                    self.colors[lang] = []
                if _contains_non_ascii(self.locations.get(lang, [])):
                    self.locations[lang] = []
                if _contains_non_ascii(self.brands.get(lang, [])):
                    self.brands[lang] = []
        except Exception:
            # On any error, use empty lists to avoid false positives
            self.item_types['si'] = []
            self.item_types['ta'] = []
            self.colors['si'] = []
            self.colors['ta'] = []
            self.locations['si'] = []
            self.locations['ta'] = []
        
        # Initialize NLP models
        try:
            # Load spaCy models for each supported language
            self.nlp_models = {}
            for lang in self.SUPPORTED_LANGUAGES:
                if lang == 'en':
                    # Prefer medium English model; gracefully fall back if unavailable
                    try:
                        self.nlp_models[lang] = spacy.load('en_core_web_md')
                    except OSError:
                        try:
                            self.nlp_models[lang] = spacy.load('en_core_web_sm')
                            if self.enable_logging:
                                logger.warning("en_core_web_md not found; using en_core_web_sm")
                        except OSError:
                            if self.enable_logging:
                                logger.warning("English spaCy model not found; using multi-language model")
                            self.nlp_models[lang] = spacy.load('en_core_web_sm')
                elif lang == 'si':
                    # Use small model for Sinhala if available, otherwise use multi-language model
                    try:
                        self.nlp_models[lang] = spacy.load('si_core_news_sm')
                    except OSError:
                        if self.enable_logging:
                            logger.warning(f"Sinhala model not found, using multi-language model")
                        self.nlp_models[lang] = spacy.load('en_core_web_sm')
                elif lang == 'ta':
                    # Use small model for Tamil if available, otherwise use multi-language model
                    try:
                        self.nlp_models[lang] = spacy.load('ta_core_news_sm')
                    except OSError:
                        if self.enable_logging:
                            logger.warning(f"Tamil model not found, using multi-language model")
                        self.nlp_models[lang] = spacy.load('en_core_web_sm')
            
            # Load BERT model and tokenizer for semantic analysis
            self.tokenizer = AutoTokenizer.from_pretrained(bert_model_name)
            self.bert_model = AutoModel.from_pretrained(bert_model_name)
            
            # Load sentence transformer for similarity scoring
            self.sentence_transformer = SentenceTransformer(sentence_transformer_model)
            
            # Load Zero-Shot Classification pipeline
            try:
                # Use a lightweight model for efficiency
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model="valhalla/distilbart-mnli-12-1",
                    device=0 if torch.cuda.is_available() else -1
                )
                if self.enable_logging:
                    logger.info("Zero-Shot Classifier loaded successfully")
            except Exception as e:
                if self.enable_logging:
                    logger.warning(f"Failed to load Zero-Shot Classifier: {str(e)}")
                self.zero_shot_classifier = None

            if self.enable_logging:
                logger.info(f"NLP models loaded successfully")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Failed to load NLP models: {str(e)}")
            raise
    

    
    def check_plausibility(self, text: str, entities: Dict) -> Dict:
        """
        Check the plausibility of the description and generate clarification questions
        if unlikely combinations are detected (e.g., "Gucci iPhone").
        
        Args:
            text: Original text description
            entities: Extracted entities dictionary
            
        Returns:
            Dict containing plausibility check results and clarification questions
        """
        questions = []
        warnings = []
        
        # Check for Fashion Brand + Tech Item combination
        # This usually implies the user meant a case/accessory, or it's a fake/custom item
        
        tech_items = ['phone', 'laptop', 'tablet', 'computer', 'camera', 'console', 'xbox', 'playstation']
        
        has_tech_item = any(item in text.lower() for item in tech_items)
        has_fashion_brand = len(entities.get('style_mentions', [])) > 0
        
        if has_tech_item and has_fashion_brand:
            fashion_brand = entities['style_mentions'][0]
            item_type = next((item for item in tech_items if item in text.lower()), "item")
            
            questions.append(
                f"You mentioned a {fashion_brand} {item_type}. "
                f"Did you mean a {fashion_brand} CASE or accessory for your {item_type}? "
                f"{fashion_brand} typically doesn't make {item_type}s."
            )
            warnings.append("Unlikely brand-item combination detected")
            
        return {
            "plausible": len(warnings) == 0,
            "warnings": warnings,
            "clarification_questions": questions
        }

    def analyze_with_llm(self, text: str) -> Dict:
        """
        Perform research-grade analysis using the LLM client.
        
        Args:
            text: The text description to analyze
            
        Returns:
            Dict containing LLM analysis results
        """
        # Return basic analysis if LLM is unavailable
        if self.llm_client is None:
            return {
                "analysis": "Basic validation (LLM unavailable)",
                "confidence": 0.5,
                "suggestions": [],
                "interpretations": []
            }
        
        try:
            # LLM enrichment is optional; never block core validation flow.
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.llm_client.analyze_text, text)
                return future.result(timeout=8)
        except FuturesTimeoutError:
            if self.enable_logging:
                logger.warning("LLM analysis timed out after 8s; continuing with base validation")
            return {
                "analysis": "Basic validation (LLM timeout)",
                "confidence": 0.5,
                "suggestions": [],
                "interpretations": []
            }
        except Exception as e:
            if self.enable_logging:
                logger.error(f"LLM analysis failed: {str(e)}")
            return {
                "error": str(e),
                "analysis": "Basic validation (LLM failed)",
                "confidence": 0.5
            }

    def validate_text(
        self,
        text: str,
        language: str = 'en',
        item_type_hint: Optional[str] = None,
        color_hint: Optional[str] = None,
        location_hint: Optional[str] = None,
    ) -> Dict:
        """Main validation pipeline that processes a text description and returns structured results.
        
        Args:
            text: The text description to validate
            language: Language code ('en', 'si', 'ta') (default: 'en')
            item_type_hint: Optional hint for the item category collected elsewhere
            color_hint: Optional hint for the item's color
            location_hint: Optional hint describing where the item was lost
            
        Returns:
            Dict containing validation results with the following structure:
            {
                "valid": bool,  # Overall validity of the description
                "completeness": {  # Completeness analysis results
                    "valid": bool,
                    "score": float,
                    "threshold": float,
                    "item_type": {"found": bool, "value": str},
                    "color": {"found": bool, "value": str},
                    "location": {"found": bool, "value": str},
                    "message": str
                },
                "coherence": {  # Semantic coherence results
                    "valid": bool,
                    "score": float,
                    "threshold": float,
                    "message": str
                },
                "entities": {  # Entity extraction results
                    "valid": bool,
                    "extracted": List[Dict],
                    "message": str
                },
                "feedback": {  # Feedback generation results
                    "suggestions": List[str],
                    "missing_elements": List[str],
                    "message": str
                },
                "clarification_questions": List[str], # New field for interactive clarifications
                "processing_time": float,  # Total processing time in seconds
                "message": str  # Overall validation message
            }
        """
        start_time = time.time()
        
        # Initialize result structure
        result = {
            "text": text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "completeness": {},
            "coherence": {},
            "entities": {},
            "overall_score": 0.0,
            "valid": False,
            "clarification_questions": []
        }
        
        try:
            # Check if language is supported
            if language not in self.SUPPORTED_LANGUAGES:
                result["feedback"] = {"message": f"Unsupported language: {language}. Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}"}
                return result
            
            # Check text length
            if len(text) > self.MAX_TEXT_LENGTH:
                result["feedback"] = {"message": f"Text exceeds maximum length of {self.MAX_TEXT_LENGTH} characters"}
                return result
            
            # Step 1: Perform completeness analysis
            completeness_result = self.check_completeness(
                text,
                language,
                item_type_hint=item_type_hint,
                color_hint=color_hint,
                location_hint=location_hint,
            )
            result["completeness"] = completeness_result
            
            # Step 2: Perform semantic coherence validation
            coherence_result = self.check_semantic_coherence(text, language)
            result["coherence"] = coherence_result
            
            # Step 3: Perform entity extraction
            entities_result = self.extract_entities(text, language)
            result["entities"] = entities_result
            
            # Step 4: Plausibility Check (New)
            plausibility_result = self.check_plausibility(text, entities_result)
            result["clarification_questions"] = plausibility_result["clarification_questions"]
            

            # Calculate overall score
            completeness_normalized = completeness_result["score"] / 100
            overall_score = (0.7 * completeness_normalized) + (0.3 * coherence_result["score"])
            result["overall_score"] = round(overall_score, 2)
            
            # Determine overall validity
            result["valid"] = overall_score >= 0.7
            
            # Generate final feedback
            result["feedback"] = completeness_result["feedback"]

            # Step 5: Research-Grade LLM Analysis (New)
            llm_result = self.analyze_with_llm(text)
            if llm_result:
                # Merge clarification questions
                if llm_result.get("clarification_needed") and llm_result.get("clarification_question"):
                    result["clarification_questions"].append(llm_result["clarification_question"])
                
                # Add reasoning to feedback
                if llm_result.get("reasoning"):
                    reasoning_msg = f"\n\nAnalysis: {llm_result['reasoning']}"
                    if isinstance(result["feedback"], dict):
                        result["feedback"]["message"] += reasoning_msg
                    else:
                        result["feedback"] += reasoning_msg
            
            # If we have clarification questions, append them to feedback message
            if result["clarification_questions"]:
                q_text = " ".join(result["clarification_questions"])
                if isinstance(result["feedback"], dict):
                    result["feedback"]["message"] += f" {q_text}"
                else:
                    result["feedback"] += f" {q_text}"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during text validation: {str(e)}")
            result["feedback"] = {"message": f"Error during validation: {str(e)}"}
        
        return result

    ITEM_KEYWORDS = {
        'phone': ['phone', 'mobile', 'iphone', 'samsung', 'smartphone', 'cell'],
        'bag': ['bag', 'backpack', 'purse', 'wallet', 'handbag', 'briefcase', 'suitcase'],
        'electronics': ['laptop', 'tablet', 'ipad', 'watch', 'airpods', 'headphones', 'earbuds', 'camera', 'kindle'],
        'accessories': ['keys', 'key', 'car key', 'fob', 'glasses', 'sunglasses', 'umbrella', 'hat', 'scarf', 'glove', 'gloves', 'ring', 'necklace'],
        'documents': ['id', 'passport', 'license', 'card', 'folder', 'notebook'],
        'clothing': ['shoes', 'shoe', 'sneaker', 'sneakers', 'boots', 'jacket', 'coat', 'shirt', 't-shirt', 'pants', 'jeans', 'sweater', 'hoodie', 'apparel', 'clothing']
    }
    COLOR_KEYWORDS = ['red', 'blue', 'black', 'white', 'green', 'yellow', 'brown', 'gray', 'pink', 'purple', 'orange', 'silver', 'gold', 'beige', 'maroon', 'navy']
    BRAND_KEYWORDS = [
        'iphone', 'samsung', 'apple', 'google', 'huawei', 'xiaomi', 'nike', 'adidas', 'gucci', 'louis vuitton', 'prada',
        'sony', 'dell', 'hp', 'lenovo', 'asus', 'acer', 'microsoft', 'nintendo', 'canon', 'nikon',
        'toyota', 'honda', 'nissan', 'suzuki', 'mazda', 'bmw', 'mercedes', 'benz', 'audi', 'ford', 'tesla', 'beats'
    ]
    LOCATION_KEYWORDS = [
        'library', 'cafeteria', 'canteen', 'classroom', 'parking', 'gym',
        'office', 'hallway', 'gate', 'station', 'building', 'lab',
        'laboratory', 'auditorium', 'corridor', 'lobby', 'entrance',
        'exit', 'restroom', 'bathroom', 'toilet', 'reception', 'park',
        'playground', 'field', 'yard', 'movie theater', 'theater',
        'cinema', 'mall', 'store', 'shop', 'restaurant', 'cafe',
        'bus stop', 'train station', 'airport', 'hospital', 'hotel',
        'church', 'museum', 'stadium', 'beach', 'market', 'supermarket',
        'bank', 'bar', 'club', 'university', 'school', 'college',
        'campus', 'dorm', 'dormitory', 'apartment', 'house', 'street',
        'road', 'bus', 'train', 'taxi', 'subway', 'metro', 'study area'
    ]
    TIME_KEYWORDS = ['yesterday', 'today', 'morning', 'afternoon', 'evening', 'night', 'ago', 'last', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'am', 'pm', 'o\'clock']

    def extract_location_phrase(self, text: str, language: str) -> Optional[str]:
        """Extract full location phrase from text using LLM-first approach.
        
        Priority:
        1. Use LLM (Gemini/Groq) for natural language extraction - best for full phrases
        2. Use spaCy NER entities (GPE, LOC, FAC) for grammar-based extraction
        3. Extract context around location keywords as fallback
        
        Args:
            text: The text to extract location from
            language: Language code ('en', 'si', 'ta')
            
        Returns:
            Full location phrase or None if no location found
        """
        try:
            # First try: Use LLM for natural language extraction (best for full phrases)
            if self.llm_client and language == 'en':
                try:
                    llm_result = self.llm_client.guide_conversation(
                        user_message=text,
                        conversation_history=[],
                        previous_extracted_info=None
                    )
                    
                    if llm_result and isinstance(llm_result.get("extracted_info"), dict):
                        llm_location = llm_result["extracted_info"].get("location", "").strip()
                        if llm_location:
                            # LLM successfully extracted location
                            if self.enable_logging:
                                logger.debug(f"LLM extracted location: '{llm_location}' from '{text}'")
                            return llm_location
                except Exception as e:
                    if self.enable_logging:
                        logger.debug(f"LLM location extraction failed, falling back: {e}")
            
            # Second try: Use spaCy NER to find location entities
            doc = self.nlp_models[language](text)
            location_entities = []
            
            # Collect all location-related entities
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC', 'FAC', 'ORG']:  # Geopolitical, Location, Facility, Organization
                    location_entities.append(ent.text.strip())
            
            # Return first substantial location entity (more than just generic words)
            for loc in location_entities:
                if len(loc) > 2 and loc.lower() not in ['the', 'at', 'in', 'on', 'near']:
                    return loc
            
            # Third try: Find keywords and extract surrounding context
            text_lower = text.lower()
            words = text.split()
            
            for keyword in self.LOCATION_KEYWORDS:
                if keyword in text_lower:
                    # Find the position of the keyword
                    keyword_words = keyword.split()
                    keyword_len = len(keyword_words)
                    
                    for i in range(len(words)):
                        # Check if keyword matches at this position
                        word_span = ' '.join(words[i:i+keyword_len]).lower()
                        if word_span == keyword:
                            # Extract 3 words before and 2 words after keyword
                            start_idx = max(0, i - 3)
                            end_idx = min(len(words), i + keyword_len + 2)
                            location_phrase = ' '.join(words[start_idx:end_idx])
                            
                            # Clean up common prefixes/suffixes
                            location_phrase = location_phrase.strip('.,!?;:')
                            # Remove leading prepositions
                            for prep in ['at the', 'in the', 'near the', 'at', 'in', 'near', 'on', 'by']:
                                if location_phrase.lower().startswith(prep + ' '):
                                    location_phrase = location_phrase[len(prep) + 1:]
                            
                            return location_phrase.strip()
            
            # Fourth try: If no keywords found, look for common location patterns
            # "at X", "in X", "near X" patterns
            import re
            location_pattern = r'(?:at|in|near|on|by)\s+([A-Za-z0-9\s\-\']+(?:cafe|restaurant|building|street|st|road|rd|floor|university|college|school|library|park|station|stop))'
            match = re.search(location_pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            return None
            
        except Exception as e:
            if self.enable_logging:
                logger.warning(f"Location phrase extraction failed: {str(e)}")
            return None

    def check_completeness(
        self,
        text: str,
        language: str,
        item_type_hint: Optional[str] = None,
        color_hint: Optional[str] = None,
        location_hint: Optional[str] = None,
    ) -> Dict:
        text_lower = text.lower()
        entities = {"item_type": [], "color": [], "location": [], "brand": []}
        tokens = [token for token in text_lower.replace(".", " ").replace(",", " ").split() if token.strip()]
        unique_tokens = set(tokens)

        def find_match(options):
            for opt in options:
                # Use exact word boundaries
                if f" {opt} " in f" {text_lower} ":
                    return opt
            return None

        item_match = None
        # Try Zero-Shot Classification first if available and language is English
        if self.zero_shot_classifier and language == 'en':
            try:
                # Augmented candidate labels: categories + specific ambiguous items
                base_categories = list(self.ITEM_KEYWORDS.keys())
                specific_items = ['wallet', 'keys', 'watch', 'laptop', 'umbrella']
                candidate_labels = base_categories + specific_items
                
                # Mapping for specific items back to categories
                item_map = {
                    'wallet': 'bag',
                    'keys': 'accessories',
                    'watch': 'electronics',
                    'laptop': 'electronics',
                    'umbrella': 'accessories'
                }

                # Classify the text
                zs_result = self.zero_shot_classifier(text, candidate_labels)
                
                if self.enable_logging:
                    logger.info(f"Zero-Shot top prediction: {zs_result['labels'][0]} (score: {zs_result['scores'][0]:.2f})")

                # Check if the top score is confident enough
                if zs_result['scores'][0] > 0.3:
                    top_label = zs_result['labels'][0]
                    
                    # Determine the final item match
                    if top_label in item_map:
                        # Map specific item to its category (or keep as specific item if preferred)
                        # Here we return the specific item as the match, so it gets added to entities
                        item_match = top_label
                    else:
                        # It's a category label
                        item_match = top_label
                    
                    if self.enable_logging:
                        logger.info(f"Zero-Shot detected item: {item_match} (score: {zs_result['scores'][0]:.2f})")
            except Exception as e:
                if self.enable_logging:
                    logger.warning(f"Zero-Shot classification failed: {str(e)}")

        # Fallback to keyword matching if Zero-Shot didn't find anything
        if not item_match:
            for keywords in self.ITEM_KEYWORDS.values():
                item_match = find_match(keywords)
                if item_match:
                    break
        
        has_item = bool(item_match)
        if not has_item and item_type_hint:
            item_match = item_type_hint
            has_item = True
        if item_match:
            entities["item_type"].append(item_match)

        color_match = find_match(self.COLOR_KEYWORDS)
        has_color = bool(color_match)
        if not has_color and color_hint:
            color_match = color_hint
            has_color = True
        if color_match:
            entities["color"].append(color_match)

        # Extract location using full phrase extraction
        location_match = self.extract_location_phrase(text, language)
        has_location = bool(location_match)
        if not has_location and location_hint:
            location_match = location_hint
            has_location = True
        if location_match:
            entities["location"].append(location_match)

        brand_match = find_match(self.BRAND_KEYWORDS)
        has_brand = bool(brand_match)
        if brand_match:
            entities["brand"].append(brand_match)

        has_time = any(time in text_lower for time in self.TIME_KEYWORDS)

        score = 0
        if has_item:
            score += 30
        if has_color:
            score += 20
        if has_location:
            score += 20
        if has_brand:
            score += 15
        if has_time:
            score += 15

        missing = []
        if not has_item:
            missing.append("item type")
        if not has_color:
            missing.append("color")
        if not has_location:
            missing.append("location")

        vagueness_reasons = []
        if len(tokens) < 5:
            vagueness_reasons.append("the description is too short")
        if len(unique_tokens) <= 3 and len(tokens) > 0:
            vagueness_reasons.append("it repeats the same words")
        if len(missing) >= 2:
            vagueness_reasons.append("it is missing details like item type, color, or location")

        if vagueness_reasons:
            feedback_message = (
                "Description appears too vague because "
                + ", ".join(vagueness_reasons)
                + ". Please mention what the item is, its color, and where you last had it."
            )
        else:
            feedback_message = f"Completeness: {score}%"
            if missing:
                feedback_message += f" - Missing: {', '.join(missing)}"
            else:
                feedback_message += " - Complete!"

        return {
            "valid": score >= 70,
            "score": score,
            "entities": entities,
            "missing_info": missing,
            "has_brand": has_brand,
            "has_time": has_time,
            "is_vague": len(vagueness_reasons) > 0,
            "vagueness_reasons": vagueness_reasons,
            "feedback": feedback_message,
        }

    def check_semantic_coherence(self, text: str, language: str) -> Dict:
        """Validate the semantic coherence of a text description using BERT embeddings.
        
        Args:
            text: The text description to validate
            language: Language code ('en', 'si', 'ta')
            
        Returns:
            Dict containing semantic coherence validation results
        """
        result = {
            "valid": False,
            "score": 0.0,
            "feedback": ""
        }
        
        try:
            # Split text into sentences
            doc = self.nlp_models[language](text)
            sentences = [sent.text for sent in doc.sents]
            
            # If there's only one sentence, it's considered coherent
            if len(sentences) <= 1:
                result["valid"] = True
                result["score"] = 1.0
                result["feedback"] = "Description is coherent"
                return result
            
            # Calculate pairwise similarity between consecutive sentences
            similarity_scores = []
            for i in range(len(sentences) - 1):
                # Get embeddings for consecutive sentences
                embeddings = self.sentence_transformer.encode(sentences[i:i+2])
                
                # Calculate cosine similarity
                similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
                similarity_scores.append(similarity)
            
            # Calculate average similarity score
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            
            # Keep coherence scoring deterministic and non-blocking.
            # The previous attention-based auxiliary signal occasionally stalled
            # on some transformer backends and blocked request completion.
            blended = float(avg_similarity)
            result["score"] = blended
            
            # Determine validity based on threshold
            result["valid"] = blended >= self.coherence_threshold
            
            # Generate message
            if result["valid"]:
                result["feedback"] = "Description is semantically coherent"
            else:
                result["feedback"] = "Description lacks semantic coherence"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during coherence validation: {str(e)}")
            result["feedback"] = f"Error during coherence validation: {str(e)}"
        
        return result




    
    PRODUCT_BRAND_MAP = {
        'iphone': 'Apple',
        'ipad': 'Apple',
        'macbook': 'Apple',
        'airpods': 'Apple',
        'apple watch': 'Apple',
        'galaxy': 'Samsung',
        'pixel': 'Google',
        'playstation': 'Sony',
        'xbox': 'Microsoft',
        'thinkpad': 'Lenovo',
        'surface': 'Microsoft',
        'kindle': 'Amazon',
        'switch': 'Nintendo',
        'walkman': 'Sony',
        'eos': 'Canon',
        'cybershot': 'Sony',
        'gopro': 'GoPro',
        'fitbit': 'Fitbit'
    }

    BRAND_CATEGORIES = {
        'manufacturer': [
            'apple', 'samsung', 'google', 'sony', 'microsoft', 'lenovo', 'dell', 'hp', 
            'asus', 'acer', 'nokia', 'motorola', 'lg', 'htc', 'huawei', 'xiaomi', 
            'oppo', 'vivo', 'oneplus', 'canon', 'nikon', 'fujifilm', 'gopro', 'fitbit',
            'bose', 'jbl', 'beats', 'nintendo', 'amazon'
        ],
        'fashion': [
            'gucci', 'prada', 'louis vuitton', 'hermes', 'chanel', 'dior', 'versace', 
            'armani', 'fendi', 'balenciaga', 'burberry', 'coach', 'michael kors', 
            'kate spade', 'supreme', 'nike', 'adidas', 'puma', 'under armour', 'zara',
            'h&m', 'uniqlo', 'levis', 'calvin klein', 'tommy hilfiger', 'ralph lauren'
        ]
    }

    def extract_entities(self, text: str, language: str) -> Dict:
        """Extract named entities from a text description using spaCy NER.
        
        Args:
            text: The text description to analyze
            language: Language code ('en', 'si', 'ta')
            
        Returns:
            Dict containing entity extraction results
        """
        result = {
            "entities": [],
            "item_mentions": [],
            "color_mentions": [],
            "location_mentions": [],
            "brand_mentions": [],
            "style_mentions": []  # New field for fashion/style brands
        }
        
        try:
            # Process text with spaCy
            doc = self.nlp_models[language](text)
            
            # Extract entities
            for ent in doc.ents:
                result["entities"].append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
            
            text_lower = text.lower()
            
            # Extract item mentions
            for item_type in self.item_types[language]:
                if item_type in text_lower:
                    result["item_mentions"].append(item_type)
            
            # Extract color mentions
            for color in self.colors[language]:
                if color in text_lower:
                    result["color_mentions"].append(color)
            
            # Extract location using full phrase extraction (not just keywords)
            location_phrase = self.extract_location_phrase(text, language)
            if location_phrase:
                result["location_mentions"].append(location_phrase)

            # ------------------------------------------------------------------
            # Enhanced Brand Detection Logic
            # ------------------------------------------------------------------
            detected_brands = set()
            detected_styles = set()
            
            # 1. Explicit Brand Detection
            # Check against known brand list
            for brand in self.brands.get(language, self.brands['en']):
                if brand and brand.lower() in text_lower:
                    # Categorize detected brand
                    if brand.lower() in self.BRAND_CATEGORIES['fashion']:
                        detected_styles.add(brand)
                    else:
                        detected_brands.add(brand)
            
            # 2. Implicit Brand Detection (Product -> Brand)
            # e.g., "iPhone" -> "Apple"
            for product, brand in self.PRODUCT_BRAND_MAP.items():
                if product in text_lower:
                    detected_brands.add(brand)
                    
            # 3. Conflict Resolution / Prioritization
            # If we have both a manufacturer and a fashion brand, the manufacturer 
            # is likely the "main" brand (e.g., "Gucci iPhone" -> Brand: Apple, Style: Gucci)
            
            # Convert sets to lists for JSON serialization
            result["brand_mentions"] = list(detected_brands)
            result["style_mentions"] = list(detected_styles)
            
            # If no manufacturer brand found but style found, and the item is typically
            # a fashion item (bag, wallet, clothing), we might want to promote style to brand.
            # But for now, keeping them separate is safer for logic.
            
            # Special Case: If "brand_mentions" is empty but we have "style_mentions",
            # and the item is NOT an electronic device, we might consider the style as the brand.
            # e.g., "Gucci bag" -> Brand: Gucci.
            # e.g., "Gucci iPhone" -> Brand: Apple (implicit), Style: Gucci.
            
            is_electronic = any(x in text_lower for x in ['phone', 'laptop', 'tablet', 'watch', 'camera', 'headphones'])
            
            if not result["brand_mentions"] and result["style_mentions"]:
                if not is_electronic:
                    # Promote style to brand for non-electronics
                    result["brand_mentions"] = result["style_mentions"]
                    result["style_mentions"] = []
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during entity extraction: {str(e)}")
        
        return result
    

    
    def batch_validate(self, texts: List[str], language: str = 'en') -> List[Dict]:
        """Validate multiple text descriptions in batch mode.
        
        Args:
            texts: List of text descriptions to validate
            language: Language code ('en', 'si', 'ta') (default: 'en')
            
        Returns:
            List of validation results for each text description
        """
        results = []
        
        for text in texts:
            result = self.validate_text(text, language)
            results.append(result)
        
        return results
    
    def save_results(self, results: Union[Dict, List[Dict]], output_path: str) -> bool:
        """Save validation results to a JSON file.
        
        Args:
            results: Validation results (single result or list of results)
            output_path: Path where the results should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            if self.enable_logging:
                logger.info(f"Validation results saved to {output_path}")
            
            return True
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error saving validation results: {str(e)}")
            
            return False

    # ------------------------------------------------------------------ #
    # Intent Classification
    # ------------------------------------------------------------------ #
    def classify_intent(self, text: str) -> Dict:
        """
        Classify whether the text is reporting a lost item, found item, or inquiry.
        
        This is critical for routing the submission to the correct workflow:
        - "lost": User reporting their own lost item
        - "found": User reporting an item they found
        - "inquiry": User asking about item status or general questions
        
        Args:
            text: The text description to classify
            
        Returns:
            Dict containing:
                - intent: "lost", "found", "inquiry", or "unknown"
                - confidence: Confidence score (0-1)
                - method: "zero_shot" or "keyword"
                - all_scores: Scores for all intents (if using zero-shot)
        """
        result = {
            "intent": "unknown",
            "confidence": 0.0,
            "method": "keyword",
            "all_scores": {}
        }
        
        # Try Zero-Shot Classification first (more accurate)
        if self.zero_shot_classifier:
            try:
                candidate_labels = [
                    "reporting a lost item",
                    "reporting a found item", 
                    "inquiry about an item"
                ]
                
                zs_result = self.zero_shot_classifier(text, candidate_labels)
                
                intent_map = {
                    "reporting a lost item": "lost",
                    "reporting a found item": "found",
                    "inquiry about an item": "inquiry"
                }
                
                top_label = zs_result['labels'][0]
                top_score = zs_result['scores'][0]
                
                result["intent"] = intent_map.get(top_label, "unknown")
                result["confidence"] = round(top_score, 3)
                result["method"] = "zero_shot"
                result["all_scores"] = {
                    intent_map.get(label, label): round(score, 3)
                    for label, score in zip(zs_result['labels'], zs_result['scores'])
                }
                
                if self.enable_logging:
                    logger.info(f"Intent classified as '{result['intent']}' with confidence {top_score:.2f}")
                
                return result
                
            except Exception as e:
                if self.enable_logging:
                    logger.warning(f"Zero-shot intent classification failed: {e}, falling back to keywords")
        
        # Fallback to keyword matching
        lower = text.lower()
        
        # Lost item indicators
        lost_keywords = [
            "i lost", "lost my", "missing", "can't find", "cannot find",
            "misplaced", "left behind", "forgot", "disappeared", "i've lost",
            "looking for my", "searching for my"
        ]
        
        # Found item indicators  
        found_keywords = [
            "i found", "found a", "found an", "someone left", "picked up",
            "discovered", "came across", "located", "is this yours",
            "turned in", "found this"
        ]
        
        # Inquiry indicators
        inquiry_keywords = [
            "have you seen", "has anyone", "did anyone", "is there",
            "status of", "update on", "any news", "checking on",
            "?", "wondering if", "do you have"
        ]
        
        # Count matches for each category
        lost_matches = sum(1 for kw in lost_keywords if kw in lower)
        found_matches = sum(1 for kw in found_keywords if kw in lower)
        inquiry_matches = sum(1 for kw in inquiry_keywords if kw in lower)
        
        # Determine intent based on keyword matches
        if lost_matches > found_matches and lost_matches > inquiry_matches:
            result["intent"] = "lost"
            result["confidence"] = min(0.9, 0.5 + lost_matches * 0.15)
        elif found_matches > lost_matches and found_matches > inquiry_matches:
            result["intent"] = "found"
            result["confidence"] = min(0.9, 0.5 + found_matches * 0.15)
        elif inquiry_matches > 0:
            result["intent"] = "inquiry"
            result["confidence"] = min(0.8, 0.4 + inquiry_matches * 0.1)
        else:
            # Default to lost if no clear indicators (most common use case)
            result["intent"] = "lost"
            result["confidence"] = 0.4
        
        result["all_scores"] = {
            "lost": lost_matches,
            "found": found_matches,
            "inquiry": inquiry_matches
        }
        
        return result

    # ------------------------------------------------------------------ #
    # Urgency / Sentiment Analysis
    # ------------------------------------------------------------------ #
    def analyze_urgency(self, text: str) -> Dict:
        """
        Detect urgency and emotional intensity in the text.
        
        Used to prioritize critical cases that need immediate attention.
        
        Args:
            text: The text description to analyze
            
        Returns:
            Dict containing:
                - urgency: "critical", "high", "medium", "low", or "normal"
                - score: Urgency score (0-1, higher = more urgent)
                - indicators: List of detected urgency keywords
                - sentiment: Detected emotional tone
        """
        result = {
            "urgency": "normal",
            "score": 0.0,
            "indicators": [],
            "sentiment": "neutral"
        }
        
        lower = text.lower()
        
        # Urgency keyword tiers with weights
        urgency_tiers = {
            "critical": {
                "keywords": [
                    "emergency", "urgent", "asap", "immediately", "critical",
                    "desperate", "life-saving", "medication", "passport",
                    "must find today", "flight in"
                ],
                "weight": 1.0,
                "sentiment": "distressed"
            },
            "high": {
                "keywords": [
                    "very important", "important", "please help", "need help",
                    "really need", "soon", "quickly", "as soon as possible",
                    "valuable", "expensive", "sentimental", "irreplaceable"
                ],
                "weight": 0.75,
                "sentiment": "anxious"
            },
            "medium": {
                "keywords": [
                    "need", "help", "hoping", "would appreciate", "looking for",
                    "worried", "concerned", "quite important"
                ],
                "weight": 0.5,
                "sentiment": "concerned"
            },
            "low": {
                "keywords": [
                    "whenever", "no rush", "if possible", "sometime",
                    "not urgent", "just wondering"
                ],
                "weight": 0.25,
                "sentiment": "calm"
            }
        }
        
        # Detect indicators from each tier
        detected_tier = None
        max_weight = 0.0
        
        for tier, data in urgency_tiers.items():
            matches = [kw for kw in data["keywords"] if kw in lower]
            if matches:
                result["indicators"].extend(matches)
                if data["weight"] > max_weight:
                    max_weight = data["weight"]
                    detected_tier = tier
                    result["sentiment"] = data["sentiment"]
        
        # Additional signals: punctuation and capitalization
        exclamation_count = text.count('!')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        if exclamation_count >= 3:
            max_weight = min(1.0, max_weight + 0.15)
            result["indicators"].append("multiple_exclamations")
        
        if caps_ratio > 0.4:
            max_weight = min(1.0, max_weight + 0.1)
            result["indicators"].append("excessive_caps")
        
        # Set final urgency level
        if detected_tier:
            result["urgency"] = detected_tier
        elif max_weight > 0.6:
            result["urgency"] = "high"
        elif max_weight > 0.3:
            result["urgency"] = "medium"
        
        result["score"] = round(max_weight, 2)
        
        if self.enable_logging and result["urgency"] in ["critical", "high"]:
            logger.info(f"High urgency detected: {result['urgency']} (score: {result['score']})")
        
        return result

    def analyze_text_enhanced(self, text: str, language: str = 'en') -> Dict:
        """
        Perform enhanced text analysis including intent and urgency.
        
        This combines the standard validation with intent classification
        and urgency detection for comprehensive text understanding.
        
        Args:
            text: The text description to analyze
            language: Language code ('en', 'si', 'ta')
            
        Returns:
            Dict containing all validation results plus intent and urgency
        """
        # Standard validation
        base_result = self.validate_text(text, language)
        
        # Add intent classification
        base_result["intent"] = self.classify_intent(text)
        
        # Add urgency analysis
        base_result["urgency"] = self.analyze_urgency(text)
        
        return base_result
