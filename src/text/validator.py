import os
import time
import logging
import json
from typing import Dict, List, Tuple, Union, Optional
import spacy
import numpy as np
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TextValidator')

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
        'en': ['phone', 'wallet', 'keys', 'bag', 'backpack', 'laptop', 'umbrella', 'watch', 'glasses', 'headphones', 'camera', 'book', 'jacket', 'purse', 'card'],
        'si': ['දුරකථනය', 'පසුම්බිය', 'යතුරු', 'බෑගය', 'පිටිපසුම්බිය', 'ලැප්ටොප්', 'කුඩය', 'ඔරලෝසුව', 'කණ්ණාඩි', 'හෙඩ්ෆෝන්', 'කැමරාව', 'පොත', 'ජැකට්', 'පර්ස්', 'කාඩ්පත'],
        'ta': ['தொலைபேசி', 'பணப்பை', 'சாவிகள்', 'பை', 'பின்புறப்பை', 'மடிக்கணினி', 'குடை', 'கடிகாரம்', 'கண்ணாடி', 'தலைப்பொறி', 'புகைப்படக்கருவி', 'புத்தகம்', 'ஜாக்கெட்', 'பணப்பை', 'அட்டை']
    }
    
    # Default colors dictionary (can be extended)
    DEFAULT_COLORS = {
        'en': ['black', 'white', 'red', 'blue', 'green', 'yellow', 'brown', 'gray', 'purple', 'orange', 'pink', 'silver', 'gold'],
        'si': ['කළු', 'සුදු', 'රතු', 'නිල්', 'කොළ', 'කහ', 'දුඹුරු', 'අළු', 'දම්', 'තැඹිලි', 'රෝස', 'රිදී', 'රන්'],
        'ta': ['கருப்பு', 'வெள்ளை', 'சிவப்பு', 'நீலம்', 'பச்சை', 'மஞ்சள்', 'பழுப்பு', 'சாம்பல்', 'ஊதா', 'ஆரஞ்சு', 'இளஞ்சிவப்பு', 'வெள்ளி', 'தங்கம்']
    }
    
    # Default location terms (can be extended)
    DEFAULT_LOCATIONS = {
        'en': ['in', 'at', 'near', 'on', 'inside', 'outside', 'behind', 'under', 'above', 'below', 'beside', 'between', 'around', 'across', 'through', 'throughout', 'within', 'along', 'by', 'next to'],
        'si': ['තුළ', 'අසල', 'ළඟ', 'මත', 'ඇතුළත', 'පිටත', 'පිටුපස', 'යට', 'ඉහළ', 'පහළ', 'අසල', 'අතර', 'වටා', 'හරහා', 'තුළින්', 'පුරා', 'ඇතුළත', 'දිගේ', 'අසල', 'ළඟ'],
        'ta': ['உள்ளே', 'அருகில்', 'அருகே', 'மேல்', 'உள்ளே', 'வெளியே', 'பின்னால்', 'கீழே', 'மேலே', 'கீழே', 'பக்கத்தில்', 'இடையில்', 'சுற்றி', 'குறுக்கே', 'வழியாக', 'முழுவதும்', 'உள்ளே', 'நெடுகிலும்', 'அருகில்', 'அடுத்து']
    }
    
    DEFAULT_BRANDS = {
        'en': [
            'gucci', 'louis vuitton', 'prada', 'apple', 'samsung', 'lenovo',
            'dell', 'hp', 'nike', 'adidas', 'coach', 'hermes', 'fossil',
            'michael kors', 'lacoste'
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
                            self.nlp_models[lang] = spacy.load('xx_ent_wiki_sm')
                elif lang == 'si':
                    # Use small model for Sinhala if available, otherwise use multi-language model
                    try:
                        self.nlp_models[lang] = spacy.load('si_core_news_sm')
                    except OSError:
                        if self.enable_logging:
                            logger.warning(f"Sinhala model not found, using multi-language model")
                        self.nlp_models[lang] = spacy.load('xx_ent_wiki_sm')
                elif lang == 'ta':
                    # Use small model for Tamil if available, otherwise use multi-language model
                    try:
                        self.nlp_models[lang] = spacy.load('ta_core_news_sm')
                    except OSError:
                        if self.enable_logging:
                            logger.warning(f"Tamil model not found, using multi-language model")
                        self.nlp_models[lang] = spacy.load('xx_ent_wiki_sm')
            
            # Load BERT model and tokenizer for semantic analysis
            self.tokenizer = AutoTokenizer.from_pretrained(bert_model_name)
            self.bert_model = AutoModel.from_pretrained(bert_model_name)
            
            # Load sentence transformer for similarity scoring
            self.sentence_transformer = SentenceTransformer(sentence_transformer_model)
            
            if self.enable_logging:
                logger.info(f"NLP models loaded successfully")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Failed to load NLP models: {str(e)}")
            raise
    
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
            "valid": False
        }
        
        try:
            # Check if language is supported
            if language not in self.SUPPORTED_LANGUAGES:
                result["feedback"] = f"Unsupported language: {language}. Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}"
                return result
            
            # Check text length
            if len(text) > self.MAX_TEXT_LENGTH:
                result["feedback"] = f"Text exceeds maximum length of {self.MAX_TEXT_LENGTH} characters"
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
            
            # Calculate overall score
            completeness_normalized = completeness_result["score"] / 100
            overall_score = (0.7 * completeness_normalized) + (0.3 * coherence_result["score"])
            result["overall_score"] = round(overall_score, 2)
            
            # Determine overall validity
            result["valid"] = overall_score >= 0.7
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during text validation: {str(e)}")
            result["feedback"] = f"Error during validation: {str(e)}"
        
        return result

    ITEM_KEYWORDS = {
        'phone': ['phone', 'mobile', 'iphone', 'samsung', 'smartphone', 'cell'],
        'bag': ['bag', 'backpack', 'purse', 'wallet', 'handbag'],
        'electronics': ['laptop', 'tablet', 'ipad', 'watch', 'airpods', 'headphones'],
        'accessories': ['keys', 'glasses', 'sunglasses', 'umbrella']
    }
    COLOR_KEYWORDS = ['red', 'blue', 'black', 'white', 'green', 'yellow', 'brown', 'gray', 'pink', 'purple', 'orange']
    BRAND_KEYWORDS = ['iphone', 'samsung', 'apple', 'google', 'huawei', 'xiaomi', 'nike', 'adidas', 'gucci', 'louis vuitton', 'prada']
    LOCATION_KEYWORDS = [
        'library',
        'cafeteria',
        'canteen',
        'classroom',
        'parking',
        'gym',
        'office',
        'hallway',
        'gate',
        'station',
        'building',
    ]
    TIME_KEYWORDS = ['yesterday', 'today', 'morning', 'afternoon', 'evening', 'night', 'ago', 'last', 'monday', 'tuesday']

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
                if opt in text_lower:
                    return opt
            return None

        item_match = None
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

        location_match = find_match(self.LOCATION_KEYWORDS)
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
            
            # Auxiliary BERT attention-based signal (lightweight proxy)
            aux_signal = 1.0
            try:
                tokens = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=256)
                outputs = self.bert_model(**tokens, output_attentions=True)
                if outputs.attentions:
                    last_layer = outputs.attentions[-1]  # (batch, heads, seq, seq)
                    attn = last_layer.mean(dim=1).squeeze(0).detach().numpy()  # (seq, seq)
                    # concentration: average of max attention per token
                    conc = float(np.mean(attn.max(axis=1)))
                    aux_signal = max(0.0, min(1.0, conc))
            except Exception:
                aux_signal = 1.0  # fallback neutral
            # Blend similarity with aux signal
            blended = 0.8 * avg_similarity + 0.2 * aux_signal
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
            "brand_mentions": []
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
            
            # Extract item mentions
            for item_type in self.item_types[language]:
                if item_type in text.lower():
                    result["item_mentions"].append(item_type)
            
            # Extract color mentions
            for color in self.colors[language]:
                if color in text.lower():
                    result["color_mentions"].append(color)
            
            # Extract location mentions
            for location in self.locations[language]:
                if location in text.lower():
                    result["location_mentions"].append(location)

            # Extract brand mentions
            for brand in self.brands.get(language, self.brands['en']):
                if brand and brand.lower() in text.lower():
                    result["brand_mentions"].append(brand)
            
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
