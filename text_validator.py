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
    
    def __init__(self, 
                 item_types: Optional[Dict[str, List[str]]] = None,
                 colors: Optional[Dict[str, List[str]]] = None,
                 locations: Optional[Dict[str, List[str]]] = None,
                 completeness_threshold: float = 0.7,
                 coherence_threshold: float = 0.6,
                 bert_model_name: str = 'bert-base-multilingual-cased',
                 sentence_transformer_model: str = 'paraphrase-multilingual-mpnet-base-v2',
                 enable_logging: bool = True,
                 vagueness_threshold: float = 0.8):
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
        self.completeness_threshold = completeness_threshold
        self.coherence_threshold = coherence_threshold
        self.enable_logging = enable_logging
        self.vagueness_threshold = vagueness_threshold
        # Generic templates for vagueness detection
        self.generic_templates = {
            'en': [
                'I lost something',
                'I lost an item',
                'I cannot find my thing',
                'I misplaced something somewhere'
            ],
            'si': ['මම දෙයක් නැතිකලා', 'මට භාණ්ඩයක් අහිමි වී ඇත'],
            'ta': ['நான் ஏதோ ஒன்றை இழந்துவிட்டேன்', 'நான் ஒரு பொருளை இழந்துவிட்டேன்']
        }
        
        # Initialize NLP models
        try:
            # Load spaCy models for each supported language
            self.nlp_models = {}
            for lang in self.SUPPORTED_LANGUAGES:
                if lang == 'en':
                    self.nlp_models[lang] = spacy.load('en_core_web_md')
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
    
    def validate_text(self, text: str, language: str = 'en') -> Dict:
        """Main validation pipeline that processes a text description and returns structured results.
        
        Args:
            text: The text description to validate
            language: Language code ('en', 'si', 'ta') (default: 'en')
            
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
            "valid": False,
            "completeness": {},
            "coherence": {},
            "entities": {},
            "feedback": {},
            "processing_time": 0,
            "message": ""
        }
        
        try:
            # Check if language is supported
            if language not in self.SUPPORTED_LANGUAGES:
                result["message"] = f"Unsupported language: {language}. Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}"
                result["processing_time"] = time.time() - start_time
                return result
            
            # Check text length
            if len(text) > self.MAX_TEXT_LENGTH:
                result["message"] = f"Text exceeds maximum length of {self.MAX_TEXT_LENGTH} characters"
                result["processing_time"] = time.time() - start_time
                return result
            
            # Step 1: Perform completeness analysis
            completeness = self.analyze_completeness(text, language)
            result["completeness"] = completeness
            
            # Step 2: Perform semantic coherence validation
            coherence = self.validate_coherence(text, language)
            result["coherence"] = coherence
            
            # Step 3: Perform entity extraction
            entities = self.extract_entities(text, language)
            result["entities"] = entities
            
            # Step 3.5: Vagueness detection
            vagueness = self.detect_vagueness(text, language)
            result["vagueness"] = vagueness
            
            # Step 3.6: Entity consistency checks
            consistency = self.check_entity_consistency(text, language, entities)
            result["consistency"] = consistency
            
            # Step 4: Generate feedback
            feedback = self.generate_feedback(text, completeness, coherence, entities, language)
            result["feedback"] = feedback
            
            # Determine overall validity
            result["valid"] = (
                completeness["valid"] and 
                coherence["valid"] and vagueness.get("valid", True) and consistency.get("valid", True)
            )
            
            if result["valid"]:
                result["message"] = "Description passed all validation checks"
            else:
                failed_checks = []
                if not completeness["valid"]:
                    failed_checks.append("completeness")
                if not coherence["valid"]:
                    failed_checks.append("coherence")
                
                result["message"] = f"Description failed validation: {', '.join(failed_checks)}"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during text validation: {str(e)}")
            result["message"] = f"Error during validation: {str(e)}"
        
        # Calculate total processing time
        result["processing_time"] = time.time() - start_time
        
        return result

    def analyze_completeness(self, text: str, language: str) -> Dict:
        """Analyze the completeness of a text description.
        
        Args:
            text: The text description to analyze
            language: Language code ('en', 'si', 'ta')
            
        Returns:
            Dict containing completeness analysis results
        """
        result = {
            "valid": False,
            "score": 0.0,
            "threshold": self.completeness_threshold,
            "item_type": {"found": False, "value": ""},
            "color": {"found": False, "value": ""},
            "location": {"found": False, "value": ""},
            "message": ""
        }
        
        try:
            # Process text with spaCy
            doc = self.nlp_models[language](text.lower())
            
            # Check for item type (40% weight)
            item_type_score = 0.0
            for item_type in self.item_types[language]:
                if item_type in text.lower():
                    result["item_type"]["found"] = True
                    result["item_type"]["value"] = item_type
                    item_type_score = 0.4
                    break
            
            # Check for color (30% weight)
            color_score = 0.0
            for color in self.colors[language]:
                if color in text.lower():
                    result["color"]["found"] = True
                    result["color"]["value"] = color
                    color_score = 0.3
                    break
            
            # Check for location (30% weight)
            location_score = 0.0
            location_found = False
            
            # First check for location terms
            for location in self.locations[language]:
                if location in text.lower():
                    location_found = True
                    result["location"]["value"] = location
                    break
            
            # Then check for location entities in spaCy
            if not location_found:
                for ent in doc.ents:
                    if ent.label_ in ["LOC", "GPE", "FAC"]:
                        location_found = True
                        result["location"]["value"] = ent.text
                        break
            
            if location_found:
                result["location"]["found"] = True
                location_score = 0.3
            
            # Calculate total completeness score
            result["score"] = item_type_score + color_score + location_score
            
            # Determine validity based on threshold
            result["valid"] = result["score"] >= self.completeness_threshold
            
            # Generate message
            if result["valid"]:
                result["message"] = "Description contains all required elements"
            else:
                missing_elements = []
                if not result["item_type"]["found"]:
                    missing_elements.append("item type")
                if not result["color"]["found"]:
                    missing_elements.append("color")
                if not result["location"]["found"]:
                    missing_elements.append("location")
                
                result["message"] = f"Description is incomplete: missing {', '.join(missing_elements)}"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during completeness analysis: {str(e)}")
            result["message"] = f"Error during completeness analysis: {str(e)}"
        
        return result

    def validate_coherence(self, text: str, language: str) -> Dict:
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
            "threshold": self.coherence_threshold,
            "message": ""
        }
        
        try:
            # Split text into sentences
            doc = self.nlp_models[language](text)
            sentences = [sent.text for sent in doc.sents]
            
            # If there's only one sentence, it's considered coherent
            if len(sentences) <= 1:
                result["valid"] = True
                result["score"] = 1.0
                result["message"] = "Description is coherent"
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
                result["message"] = "Description is semantically coherent"
            else:
                result["message"] = "Description lacks semantic coherence"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during coherence validation: {str(e)}")
            result["message"] = f"Error during coherence validation: {str(e)}"
        
        return result

    def detect_vagueness(self, text: str, language: str) -> Dict:
        """Detect vagueness by comparing to generic templates. Higher similarity => more vague.
        """
        result = {
            "valid": True,
            "score": 0.0,
            "threshold": self.vagueness_threshold,
            "message": ""
        }
        try:
            templates = self.generic_templates.get(language, self.generic_templates['en'])
            emb = self.sentence_transformer.encode([text] + templates)
            text_emb = emb[0]
            sims = []
            for i in range(1, len(emb)):
                s = float(np.dot(text_emb, emb[i]) / (np.linalg.norm(text_emb) * np.linalg.norm(emb[i])))
                sims.append(s)
            max_sim = max(sims) if sims else 0.0
            result["score"] = max_sim
            result["valid"] = max_sim < self.vagueness_threshold
            result["message"] = "Description is specific" if result["valid"] else "Description appears too generic"
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during vagueness detection: {str(e)}")
            result["message"] = f"Error during vagueness detection: {str(e)}"
        return result

    def check_entity_consistency(self, text: str, language: str, entities: Dict) -> Dict:
        """Basic consistency checks for conflicting attributes (e.g., multiple colors/locations)."""
        result = {
            "valid": True,
            "issues": [],
            "message": ""
        }
        try:
            # Colors mentioned
            colors_found = [c for c in self.colors[language] if c in text.lower()]
            if len(set(colors_found)) > 1:
                result["valid"] = False
                result["issues"].append({"type": "color_conflict", "values": list(set(colors_found))})
            # Locations: multiple explicit location prepositions
            locations_found = [l for l in self.locations[language] if l in text.lower()]
            if len(set(locations_found)) > 2:
                result["valid"] = False
                result["issues"].append({"type": "location_conflict", "values": list(set(locations_found))})
            result["message"] = "No conflicts detected" if result["valid"] else "Potential conflicts detected"
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during consistency checks: {str(e)}")
            result["message"] = f"Error during consistency checks: {str(e)}"
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
            "valid": False,
            "extracted": [],
            "message": ""
        }
        
        try:
            # Process text with spaCy
            doc = self.nlp_models[language](text)
            
            # Extract entities
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
            
            result["extracted"] = entities
            
            # Determine validity based on number of entities
            result["valid"] = len(entities) > 0
            
            # Generate message
            if result["valid"]:
                result["message"] = f"Extracted {len(entities)} entities from description"
            else:
                result["message"] = "No entities found in description"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during entity extraction: {str(e)}")
            result["message"] = f"Error during entity extraction: {str(e)}"
        
        return result
    
    def generate_feedback(self, text: str, completeness: Dict, coherence: Dict, entities: Dict, language: str) -> Dict:
        """Generate constructive feedback for incomplete descriptions.
        
        Args:
            text: The text description
            completeness: Completeness analysis results
            coherence: Semantic coherence validation results
            entities: Entity extraction results
            language: Language code ('en', 'si', 'ta')
            
        Returns:
            Dict containing feedback generation results
        """
        result = {
            "suggestions": [],
            "missing_elements": [],
            "message": ""
        }
        
        try:
            # Identify missing elements
            missing_elements = []
            if not completeness["item_type"]["found"]:
                missing_elements.append("item type")
            if not completeness["color"]["found"]:
                missing_elements.append("color")
            if not completeness["location"]["found"]:
                missing_elements.append("location")
            
            result["missing_elements"] = missing_elements
            
            # Generate suggestions based on missing elements
            suggestions = []
            
            if language == 'en':
                if "item type" in missing_elements:
                    suggestions.append("Please specify what type of item you lost (e.g., phone, wallet, keys)")
                if "color" in missing_elements:
                    suggestions.append("Include the color of the item to help with identification")
                if "location" in missing_elements:
                    suggestions.append("Mention where you might have lost the item (e.g., in the library, near the cafeteria)")
                if not coherence["valid"]:
                    suggestions.append("Try to make your description more coherent and focused on the lost item")
            elif language == 'si':
                if "item type" in missing_elements:
                    suggestions.append("ඔබ අහිමි කළ භාණ්ඩයේ වර්ගය සඳහන් කරන්න (උදා: දුරකථනය, පසුම්බිය, යතුරු)")
                if "color" in missing_elements:
                    suggestions.append("හඳුනාගැනීමට උපකාරී වීම සඳහා භාණ්ඩයේ වර්ණය ඇතුළත් කරන්න")
                if "location" in missing_elements:
                    suggestions.append("ඔබ භාණ්ඩය අහිමි වූ ස්ථානය සඳහන් කරන්න (උදා: පුස්තකාලය තුළ, ආපන ශාලාව අසල)")
                if not coherence["valid"]:
                    suggestions.append("ඔබේ විස්තරය වඩාත් සම්බන්ධිත හා අහිමි වූ භාණ්ඩය කෙරෙහි අවධානය යොමු කිරීමට උත්සාහ කරන්න")
            elif language == 'ta':
                if "item type" in missing_elements:
                    suggestions.append("நீங்கள் தொலைத்த பொருளின் வகையைக் குறிப்பிடவும் (எ.கா., தொலைபேசி, பணப்பை, சாவிகள்)")
                if "color" in missing_elements:
                    suggestions.append("அடையாளம் காண உதவ பொருளின் நிறத்தைச் சேர்க்கவும்")
                if "location" in missing_elements:
                    suggestions.append("நீங்கள் பொருளை எங்கே தொலைத்திருக்கலாம் என்பதைக் குறிப்பிடவும் (எ.கா., நூலகத்தில், உணவகத்திற்கு அருகில்)")
                if not coherence["valid"]:
                    suggestions.append("உங்கள் விளக்கத்தை மேலும் ஒத்திசைவாகவும், தொலைந்த பொருளில் கவனம் செலுத்தவும் முயற்சிக்கவும்")
            
            result["suggestions"] = suggestions
            
            # Generate overall message
            if not missing_elements and coherence["valid"]:
                result["message"] = "Your description is complete and coherent"
            else:
                result["message"] = "Please improve your description with the provided suggestions"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during feedback generation: {str(e)}")
            result["message"] = f"Error during feedback generation: {str(e)}"
        
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
