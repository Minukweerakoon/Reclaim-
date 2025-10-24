import os
import time
import logging
import json
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
import torch
from sentence_transformers import SentenceTransformer
from datetime import datetime
from text_validator import TextValidator
from audio_validator import AudioValidator
from clip_validator import CLIPValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MultimodalValidator')

class MultimodalValidator:
    """An advanced multi-modal consistency validation system integrating text, audio, and image inputs.
    
    This class provides methods to validate consistency across different modalities:
    - Combines CLIP, BERT, and Whisper results into unified consistency scoring
    - Implements voice-text semantic similarity using sentence transformers
    - Validates location and temporal consistency across modalities
    - Creates adaptive confidence scoring based on input quality
    - Provides intelligent routing based on confidence thresholds
    
    The validation pipeline returns structured results in JSON format with detailed breakdown
    of individual and cross-modal scores, routing decisions, and confidence intervals.
    """
    
    # Default weights for different modalities
    DEFAULT_WEIGHTS = {
        'image': 0.25,  # Image validation weight
        'text': 0.25,   # Text validation weight
        'voice': 0.20,  # Voice/audio validation weight
        'cross_modal': 0.30  # Cross-modal consistency weight
    }
    
    # Confidence thresholds for routing
    CONFIDENCE_THRESHOLDS = {
        'high': 0.85,    # High confidence threshold (≥85%)
        'medium': 0.70,  # Medium confidence threshold (70-84%)
        'low': 0.0       # Low confidence threshold (<70%)
    }
    
    # Performance requirements
    MAX_PROCESSING_TIME = 3.0  # Maximum processing time in seconds
    
    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 confidence_thresholds: Optional[Dict[str, float]] = None,
                 text_validator_params: Optional[Dict] = None,
                 audio_validator_params: Optional[Dict] = None,
                 clip_validator_params: Optional[Dict] = None,
                 sentence_transformer_model: str = 'paraphrase-multilingual-mpnet-base-v2',
                 enable_bayesian_estimation: bool = True,
                 enable_logging: bool = True):
        """Initialize the MultimodalValidator with configurable parameters.
        
        Args:
            weights: Dictionary of weights for different modalities (default: None, uses DEFAULT_WEIGHTS)
            confidence_thresholds: Dictionary of confidence thresholds for routing (default: None, uses CONFIDENCE_THRESHOLDS)
            text_validator_params: Parameters for TextValidator initialization (default: None)
            audio_validator_params: Parameters for AudioValidator initialization (default: None)
            clip_validator_params: Parameters for CLIPValidator initialization (default: None)
            sentence_transformer_model: Name of the sentence transformer model for cross-modal similarity (default: 'paraphrase-multilingual-mpnet-base-v2')
            enable_bayesian_estimation: Whether to use Bayesian confidence estimation (default: True)
            enable_logging: Whether to enable logging (default: True)
        """
        self.weights = weights if weights is not None else self.DEFAULT_WEIGHTS
        self.confidence_thresholds = confidence_thresholds if confidence_thresholds is not None else self.CONFIDENCE_THRESHOLDS
        self.enable_bayesian_estimation = enable_bayesian_estimation
        self.enable_logging = enable_logging
        
        # Normalize weights to ensure they sum to 1.0
        total_weight = sum(self.weights.values())
        if total_weight != 1.0:
            for key in self.weights:
                self.weights[key] /= total_weight
        
        # Initialize validators
        try:
            # Initialize TextValidator
            text_validator_kwargs = text_validator_params if text_validator_params is not None else {}
            self.text_validator = TextValidator(**text_validator_kwargs)
            
            # Initialize AudioValidator
            audio_validator_kwargs = audio_validator_params if audio_validator_params is not None else {}
            self.audio_validator = AudioValidator(**audio_validator_kwargs)
            
            # Initialize CLIPValidator
            clip_validator_kwargs = clip_validator_params if clip_validator_params is not None else {}
            self.clip_validator = CLIPValidator(**clip_validator_kwargs)
            
            # Initialize sentence transformer for cross-modal similarity
            self.sentence_transformer = SentenceTransformer(sentence_transformer_model)
            
            if self.enable_logging:
                logger.info("Multimodal validator initialized successfully")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Failed to initialize multimodal validator: {str(e)}")
            raise
    
    def validate(self, 
                 text: Optional[str] = None, 
                 image_path: Optional[str] = None, 
                 audio_path: Optional[str] = None,
                 language: str = 'en',
                 progress_cb: Optional[Any] = None) -> Dict:
        """Main validation pipeline that processes multimodal inputs and returns structured results.
        
        Args:
            text: Text description (optional)
            image_path: Path to image file (optional)
            audio_path: Path to audio file (optional)
            language: Language code for text processing (default: 'en')
            
        Returns:
            Dict containing validation results with detailed breakdown of scores and confidence intervals
        """
        start_time = time.time()
        
        # Initialize result structure
        result = {
            "valid": False,
            "confidence": 0.0,
            "confidence_interval": [0.0, 0.0],
            "routing": "",
            "modal_scores": {
                "text": {},
                "image": {},
                "audio": {},
                "cross_modal": {}
            },
            "consistency": {
                "temporal": {},
                "geographic": {},
                "entity": {},
                "contradictions": []
            },
            "feedback": {
                "suggestions": [],
                "missing_elements": [],
                "message": ""
            },
            "processing_time": 0.0,
            "message": ""
        }
        
        try:
            # Check if at least one modality is provided
            if text is None and image_path is None and audio_path is None:
                result["message"] = "Error: At least one modality (text, image, or audio) must be provided"
                result["processing_time"] = time.time() - start_time
                return result
            
            # Track available modalities
            available_modalities = []
            if text is not None:
                available_modalities.append("text")
            if image_path is not None:
                available_modalities.append("image")
            if audio_path is not None:
                available_modalities.append("audio")
            
            # Step 1: Validate individual modalities
            text_result = self._validate_text(text, language) if text is not None else None
            if progress_cb:
                try:
                    progress_cb({"type": "stage", "stage": "text", "message": "Text validated"})
                except Exception:
                    pass
            image_result = self._validate_image(image_path) if image_path is not None else None
            if progress_cb:
                try:
                    progress_cb({"type": "stage", "stage": "image", "message": "Image validated"})
                except Exception:
                    pass
            audio_result = self._validate_audio(audio_path) if audio_path is not None else None
            if progress_cb:
                try:
                    progress_cb({"type": "stage", "stage": "audio", "message": "Audio validated"})
                except Exception:
                    pass
            
            # Store individual modal results
            if text_result:
                result["modal_scores"]["text"] = text_result
            if image_result:
                result["modal_scores"]["image"] = image_result
            if audio_result:
                result["modal_scores"]["audio"] = audio_result
            
            # Step 2: Validate cross-modal consistency
            cross_modal_result = self._validate_cross_modal(text, image_path, audio_path, language)
            result["modal_scores"]["cross_modal"] = cross_modal_result
            if progress_cb:
                try:
                    progress_cb({"type": "stage", "stage": "cross_modal", "message": "Cross-modal validated"})
                except Exception:
                    pass
            
            # Step 3: Validate temporal and geographic consistency
            if text is not None or (audio_result and audio_result.get("transcription", {}).get("text")):
                text_content = text if text else audio_result["transcription"]["text"]
                consistency = self._validate_consistency(text_content, language)
                result["consistency"] = consistency
            
            # Step 4: Calculate overall confidence score with Bayesian estimation
            confidence, confidence_interval = self._calculate_confidence(result)
            result["confidence"] = confidence
            result["confidence_interval"] = confidence_interval
            if progress_cb:
                try:
                    progress_cb({"type": "confidence_update", "confidence": confidence, "ci": confidence_interval})
                except Exception:
                    pass
            # Contribution breakdown (per available modality)
            try:
                contribution = {}
                for k in ["text", "image", "audio", "cross_modal"]:
                    if k in result["modal_scores"] and result["modal_scores"][k]:
                        score = result["modal_scores"][k].get("confidence", 0.0)
                        w = self.weights.get(k if k != "cross_modal" else "cross_modal", 0.0)
                        contribution[k] = {"score": score, "weight": w, "weighted": score * (w or 0.0)}
                result["contribution_breakdown"] = contribution
            except Exception:
                result["contribution_breakdown"] = {}
            
            # Step 5: Determine routing based on confidence thresholds
            if confidence >= self.confidence_thresholds["high"]:
                routing = "high"
            elif confidence >= self.confidence_thresholds["medium"]:
                routing = "medium"
            else:
                routing = "low"
            result["routing"] = routing
            
            # Step 6: Generate comprehensive feedback
            feedback = self._generate_feedback(result)
            result["feedback"] = feedback
            result["explain"] = self._build_explain(result)
            
            # Determine overall validity
            # A result is valid if confidence is at least medium threshold
            result["valid"] = confidence >= self.confidence_thresholds["medium"]
            
            if result["valid"]:
                result["message"] = "Multimodal validation passed with confidence level: " + routing
            else:
                result["message"] = "Multimodal validation failed with confidence level: " + routing
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during multimodal validation: {str(e)}")
            result["message"] = f"Error during validation: {str(e)}"
            
            # Implement graceful degradation
            if "modal_scores" in result:
                # Use available individual modal scores if any
                valid_scores = []
                if "text" in result["modal_scores"] and result["modal_scores"]["text"].get("valid", False):
                    valid_scores.append(result["modal_scores"]["text"].get("confidence", 0.0))
                if "image" in result["modal_scores"] and result["modal_scores"]["image"].get("valid", False):
                    valid_scores.append(result["modal_scores"]["image"].get("confidence", 0.0))
                if "audio" in result["modal_scores"] and result["modal_scores"]["audio"].get("valid", False):
                    valid_scores.append(result["modal_scores"]["audio"].get("confidence", 0.0))
                
                if valid_scores:
                    result["confidence"] = sum(valid_scores) / len(valid_scores)
                    result["valid"] = result["confidence"] >= self.confidence_thresholds["medium"]
                    result["message"] += " (degraded mode)"
        
        # Calculate total processing time
        processing_time = time.time() - start_time
        result["processing_time"] = processing_time
        
        # Check if processing time exceeds maximum
        if processing_time > self.MAX_PROCESSING_TIME and self.enable_logging:
            logger.warning(f"Processing time ({processing_time:.2f}s) exceeds maximum ({self.MAX_PROCESSING_TIME}s)")
        
        return result

    def _build_explain(self, result: Dict) -> Dict:
        explain = {
            "weights": self.weights,
            "reasons": {},
        }
        try:
            if "text" in result["modal_scores"] and result["modal_scores"]["text"]:
                t = result["modal_scores"]["text"]
                explain["reasons"]["text"] = {
                    "completeness": t.get("completeness", {}),
                    "coherence": t.get("coherence", {}),
                    "vagueness": t.get("vagueness", {}),
                    "entities": t.get("entities", {}),
                    "consistency": t.get("consistency", {})
                }
            if "image" in result["modal_scores"] and result["modal_scores"]["image"]:
                i = result["modal_scores"]["image"]
                explain["reasons"]["image"] = {
                    "blur_detection": i.get("blur_detection", {}),
                    "object_detection": i.get("object_detection", {}),
                    "privacy_protection": i.get("privacy_protection", {}),
                    "alignment": i.get("alignment", {})
                }
            if "audio" in result["modal_scores"] and result["modal_scores"]["audio"]:
                a = result["modal_scores"]["audio"]
                explain["reasons"]["audio"] = {
                    "audio_quality": a.get("audio_quality", {}),
                    "transcription": a.get("transcription", {})
                }
            if "cross_modal" in result["modal_scores"] and result["modal_scores"]["cross_modal"]:
                explain["reasons"]["cross_modal"] = result["modal_scores"]["cross_modal"]
            explain["contributions"] = result.get("contribution_breakdown", {})
        except Exception:
            pass
        return explain
    
    def _validate_text(self, text: str, language: str) -> Dict:
        """Validate text using TextValidator.
        
        Args:
            text: Text to validate
            language: Language code
            
        Returns:
            Dict containing text validation results
        """
        try:
            # Call TextValidator
            text_result = self.text_validator.validate_text(text, language)
            
            # Extract confidence from completeness and coherence scores
            completeness_score = text_result["completeness"].get("score", 0.0)
            coherence_score = text_result["coherence"].get("score", 0.0)
            
            # Calculate weighted confidence score
            confidence = 0.6 * completeness_score + 0.4 * coherence_score
            
            # Add confidence to result
            text_result["confidence"] = confidence
            
            return text_result
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during text validation: {str(e)}")
            return {
                "valid": False,
                "confidence": 0.0,
                "message": f"Error during text validation: {str(e)}"
            }
    
    def _validate_image(self, image_path: str) -> Dict:
        """Validate image using CLIPValidator.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict containing image validation results
        """
        try:
            # For now, we'll just validate the file
            # In a complete implementation, you would use a dedicated ImageValidator
            image_result = self.clip_validator.validate_file(image_path)
            
            # Add confidence based on file validation
            image_result["confidence"] = 1.0 if image_result["valid"] else 0.0
            
            return image_result
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during image validation: {str(e)}")
            return {
                "valid": False,
                "confidence": 0.0,
                "message": f"Error during image validation: {str(e)}"
            }
    
    def _validate_audio(self, audio_path: str) -> Dict:
        """Validate audio using AudioValidator.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict containing audio validation results
        """
        try:
            # Call AudioValidator
            audio_result = self.audio_validator.validate_audio(audio_path)
            
            # Extract confidence from transcription confidence
            transcription_confidence = audio_result["transcription"].get("confidence", 0.0)
            
            # Calculate audio quality score
            audio_quality = audio_result["audio_quality"]
            quality_score = 0.0
            if audio_quality["valid"]:
                # Normalize SNR to 0-1 range (assuming max SNR of 60dB)
                snr_score = min(audio_quality.get("snr", 0.0) / 60.0, 1.0)
                clarity_score = audio_quality.get("clarity", 0.0)
                quality_score = 0.5 * snr_score + 0.5 * clarity_score
            
            # Calculate weighted confidence score
            confidence = 0.7 * transcription_confidence + 0.3 * quality_score
            
            # Add confidence to result
            audio_result["confidence"] = confidence
            
            return audio_result
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during audio validation: {str(e)}")
            return {
                "valid": False,
                "confidence": 0.0,
                "message": f"Error during audio validation: {str(e)}"
            }
    
    def _validate_cross_modal(self, text: Optional[str], image_path: Optional[str], audio_path: Optional[str], language: str) -> Dict:
        """Validate cross-modal consistency between text, image, and audio.
        
        Args:
            text: Text description (optional)
            image_path: Path to image file (optional)
            audio_path: Path to audio file (optional)
            language: Language code
            
        Returns:
            Dict containing cross-modal validation results
        """
        result = {
            "valid": False,
            "confidence": 0.0,
            "scores": {},
            "message": ""
        }
        
        try:
            # Track available pairs for cross-modal validation
            available_pairs = []
            
            # Get text from audio transcription if text is not provided
            audio_text = None
            if audio_path and not text:
                audio_result = self.audio_validator.validate_audio(audio_path)
                if audio_result["transcription"]["valid"]:
                    audio_text = audio_result["transcription"]["text"]
            
            # Text-Image consistency using CLIP
            if text and image_path:
                available_pairs.append("text-image")
                clip_result = self.clip_validator.validate_alignment(image_path, text)
                result["scores"]["text-image"] = {
                    "similarity": clip_result["alignment"]["similarity"],
                    "confidence_interval": clip_result["alignment"]["confidence_interval"],
                    "valid": clip_result["alignment"]["valid"]
                }
            
            # Audio-Image consistency using CLIP with transcribed text
            if audio_text and image_path:
                available_pairs.append("audio-image")
                clip_result = self.clip_validator.validate_alignment(image_path, audio_text)
                result["scores"]["audio-image"] = {
                    "similarity": clip_result["alignment"]["similarity"],
                    "confidence_interval": clip_result["alignment"]["confidence_interval"],
                    "valid": clip_result["alignment"]["valid"]
                }
            
            # Text-Audio consistency using sentence transformers
            if text and audio_path and audio_text:
                available_pairs.append("text-audio")
                # Encode both texts
                embeddings = self.sentence_transformer.encode([text, audio_text])
                # Calculate cosine similarity
                similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
                # Determine validity based on threshold (0.7 is a reasonable threshold)
                valid = similarity >= 0.7
                result["scores"]["text-audio"] = {
                    "similarity": similarity,
                    "valid": valid
                }
            
            # Calculate overall cross-modal confidence
            if available_pairs:
                # Calculate average similarity across all pairs
                similarities = [result["scores"][pair]["similarity"] for pair in available_pairs]
                avg_similarity = sum(similarities) / len(similarities)
                
                # Count valid pairs
                valid_pairs = sum(1 for pair in available_pairs if result["scores"][pair]["valid"])
                
                # Overall validity requires majority of pairs to be valid
                result["valid"] = valid_pairs >= len(available_pairs) / 2
                result["confidence"] = avg_similarity
                
                if result["valid"]:
                    result["message"] = "Cross-modal consistency validation passed"
                else:
                    result["message"] = "Cross-modal consistency validation failed"
            else:
                result["message"] = "No modality pairs available for cross-modal validation"
        
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during cross-modal validation: {str(e)}")
            result["message"] = f"Error during cross-modal validation: {str(e)}"
        
        return result
    
    def _validate_consistency(self, text: str, language: str) -> Dict:
        """Validate temporal and geographic consistency in text.
        
        Args:
            text: Text to validate
            language: Language code
            
        Returns:
            Dict containing consistency validation results
        """
        result = {
            "temporal": {
                "valid": True,
                "references": [],
                "message": ""
            },
            "geographic": {
                "valid": True,
                "references": [],
                "message": ""
            },
            "entity": {
                "valid": True,
                "relationships": [],
                "message": ""
            },
            "contradictions": []
        }
        
        try:
            # Use spaCy for entity extraction and analysis
            doc = self.text_validator.nlp_models[language](text)
            
            # Extract temporal references
            temporal_entities = [ent for ent in doc.ents if ent.label_ in ["DATE", "TIME"]]
            result["temporal"]["references"] = [
                {"text": ent.text, "type": ent.label_} for ent in temporal_entities
            ]
            
            # Extract geographic references
            geo_entities = [ent for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"]]
            result["geographic"]["references"] = [
                {"text": ent.text, "type": ent.label_} for ent in geo_entities
            ]
            
            # Extract entity relationships
            # This is a simplified approach - in a real implementation, you would use
            # more sophisticated relationship extraction techniques
            entities = [ent for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "PRODUCT"]]
            
            # Check for contradictions (simplified approach)
            # In a real implementation, you would use more sophisticated contradiction detection
            sentences = [sent.text for sent in doc.sents]
            contradictions = []
            
            # Simple negation detection
            for i, sent1 in enumerate(sentences):
                for sent2 in sentences[i+1:]:
                    # Check if one sentence contains negation of a statement in another
                    # This is a very simplified approach
                    if ("not" in sent1 and any(word in sent2 for word in sent1.split() if word != "not")) or \
                       ("not" in sent2 and any(word in sent1 for word in sent2.split() if word != "not")):
                        contradictions.append({
                            "sentence1": sent1,
                            "sentence2": sent2,
                            "severity": "medium"
                        })
            
            result["contradictions"] = contradictions
            
            # Set validity based on contradictions
            if contradictions:
                result["temporal"]["valid"] = False
                result["temporal"]["message"] = "Temporal contradictions detected"
                result["geographic"]["valid"] = False
                result["geographic"]["message"] = "Geographic contradictions detected"
            else:
                result["temporal"]["message"] = "No temporal contradictions detected"
                result["geographic"]["message"] = "No geographic contradictions detected"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during consistency validation: {str(e)}")
            result["temporal"]["message"] = f"Error during temporal consistency validation: {str(e)}"
            result["geographic"]["message"] = f"Error during geographic consistency validation: {str(e)}"
        
        return result
    
    def _calculate_confidence(self, result: Dict) -> Tuple[float, List[float]]:
        """Calculate overall confidence score with Bayesian estimation.
        
        Args:
            result: Validation result dictionary
            
        Returns:
            Tuple containing confidence score and confidence interval
        """
        try:
            # Extract individual confidence scores
            confidence_scores = {}
            
            # Text confidence
            if "text" in result["modal_scores"] and result["modal_scores"]["text"]:
                confidence_scores["text"] = result["modal_scores"]["text"].get("confidence", 0.0)
            
            # Image confidence
            if "image" in result["modal_scores"] and result["modal_scores"]["image"]:
                confidence_scores["image"] = result["modal_scores"]["image"].get("confidence", 0.0)
            
            # Audio confidence
            if "audio" in result["modal_scores"] and result["modal_scores"]["audio"]:
                confidence_scores["audio"] = result["modal_scores"]["audio"].get("confidence", 0.0)
            
            # Cross-modal confidence
            if "cross_modal" in result["modal_scores"] and result["modal_scores"]["cross_modal"]:
                confidence_scores["cross_modal"] = result["modal_scores"]["cross_modal"].get("confidence", 0.0)
            
            # Calculate weighted confidence score
            weighted_confidence = 0.0
            total_weight = 0.0
            
            for modality, score in confidence_scores.items():
                if modality in self.weights:
                    weighted_confidence += score * self.weights[modality]
                    total_weight += self.weights[modality]
            
            # Normalize if not all modalities are available
            if total_weight > 0:
                weighted_confidence /= total_weight
            
            # Calculate confidence interval using Bayesian estimation
            if self.enable_bayesian_estimation:
                # Simplified Bayesian approach - in a real implementation, you would use
                # more sophisticated Bayesian methods
                
                # Calculate standard error based on number of modalities and their agreement
                n_modalities = len(confidence_scores)
                if n_modalities > 1:
                    # Calculate variance of scores
                    variance = np.var(list(confidence_scores.values()))
                    # Standard error decreases with more modalities and increases with variance
                    std_error = np.sqrt(variance / n_modalities)
                else:
                    # Default standard error for single modality
                    std_error = 0.1
                
                # 95% confidence interval
                lower_bound = max(0.0, weighted_confidence - 1.96 * std_error)
                upper_bound = min(1.0, weighted_confidence + 1.96 * std_error)
                confidence_interval = [lower_bound, upper_bound]
            else:
                # Simple confidence interval without Bayesian estimation
                confidence_interval = [max(0.0, weighted_confidence - 0.1), min(1.0, weighted_confidence + 0.1)]
            
            return weighted_confidence, confidence_interval
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during confidence calculation: {str(e)}")
            return 0.0, [0.0, 0.0]
    
    def _generate_feedback(self, result: Dict) -> Dict:
        """Generate comprehensive feedback based on validation results.
        
        Args:
            result: Validation result dictionary
            
        Returns:
            Dict containing feedback information
        """
        feedback = {
            "suggestions": [],
            "missing_elements": [],
            "message": ""
        }
        
        try:
            # Collect missing elements from text validation
            if "text" in result["modal_scores"] and "completeness" in result["modal_scores"]["text"]:
                completeness = result["modal_scores"]["text"]["completeness"]
                if not completeness.get("valid", True):
                    if "item_type" in completeness and not completeness["item_type"].get("found", True):
                        feedback["missing_elements"].append("item type")
                    if "color" in completeness and not completeness["color"].get("found", True):
                        feedback["missing_elements"].append("color")
                    if "location" in completeness and not completeness["location"].get("found", True):
                        feedback["missing_elements"].append("location")
            
            # Collect suggestions from individual validators
            if "text" in result["modal_scores"] and "feedback" in result["modal_scores"]["text"]:
                text_feedback = result["modal_scores"]["text"]["feedback"]
                if "suggestions" in text_feedback:
                    feedback["suggestions"].extend(text_feedback["suggestions"])
            
            if "audio" in result["modal_scores"] and "recommendations" in result["modal_scores"]["audio"]:
                feedback["suggestions"].extend(result["modal_scores"]["audio"]["recommendations"])
            
            # Add cross-modal consistency suggestions
            if "cross_modal" in result["modal_scores"] and not result["modal_scores"]["cross_modal"].get("valid", True):
                scores = result["modal_scores"]["cross_modal"].get("scores", {})
                
                if "text-image" in scores and not scores["text-image"].get("valid", True):
                    feedback["suggestions"].append("The text description does not match the image content. Please ensure they are consistent.")
                
                if "audio-image" in scores and not scores["audio-image"].get("valid", True):
                    feedback["suggestions"].append("The audio description does not match the image content. Please ensure they are consistent.")
                
                if "text-audio" in scores and not scores["text-audio"].get("valid", True):
                    feedback["suggestions"].append("The text and audio descriptions do not match. Please ensure they are consistent.")
            
            # Add consistency-related suggestions
            if result["consistency"]["contradictions"]:
                feedback["suggestions"].append("Contradictory information detected. Please ensure consistency across your description.")
            
            # Generate overall feedback message
            if feedback["missing_elements"]:
                feedback["message"] = f"Please provide the following missing information: {', '.join(feedback['missing_elements'])}"
            elif feedback["suggestions"]:
                feedback["message"] = "Please consider the provided suggestions to improve consistency."
            else:
                feedback["message"] = "No specific improvements needed."
            
            return feedback
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during feedback generation: {str(e)}")
            feedback["message"] = f"Error during feedback generation: {str(e)}"
            return feedback
