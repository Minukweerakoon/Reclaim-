import os
import time
import logging
import json
from typing import Dict, List, Tuple, Union, Optional, Any
import numpy as np
import torch
import cv2
from PIL import Image
import clip
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CLIPValidator')

class CLIPValidator:
    """A sophisticated cross-modal consistency validation system using CLIP embeddings.
    
    This class provides methods to validate semantic alignment between images and text:
    - CLIP model integration for image-text semantic alignment
    - Similarity scoring with configurable thresholds
    - Batch processing for multiple image-text pairs
    - Detailed mismatch detection and explanation system
    
    The validation pipeline returns structured results in JSON format.
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Available CLIP model variants
    AVAILABLE_MODELS = {
        'ViT-B/32': 'ViT-B/32',
        'ViT-L/14': 'ViT-L/14',
        'RN50': 'RN50'
    }
    
    # Common attributes for mismatch detection
    ATTRIBUTE_CATEGORIES = {
        'color': [
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
            'brown', 'black', 'white', 'gray', 'silver', 'gold'
        ],
        'object_type': [
            'phone', 'wallet', 'keys', 'bag', 'backpack', 'laptop', 'umbrella',
            'watch', 'glasses', 'headphones', 'camera', 'book', 'jacket', 'purse', 'card'
        ],
        'brand': [
            'Apple', 'Samsung', 'Google', 'Sony', 'Nike', 'Adidas', 'Dell',
            'HP', 'Lenovo', 'Canon', 'Nikon', 'Microsoft', 'LG', 'Asus'
        ]
    }
    
    def __init__(self, 
                 similarity_threshold: float = 0.85,
                 model_name: str = 'ViT-B/32',
                 enable_gpu: bool = True,
                 cache_size: int = 100,
                 enable_logging: bool = True):
        """Initialize the CLIPValidator with configurable parameters.
        
        Args:
            similarity_threshold: Threshold for cosine similarity (default: 0.85)
            model_name: CLIP model variant to use (default: 'ViT-B/32')
            enable_gpu: Whether to use GPU acceleration if available (default: True)
            cache_size: Size of the embedding cache (default: 100)
            enable_logging: Whether to enable logging (default: True)
        """
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name
        self.enable_gpu = enable_gpu
        self.cache_size = cache_size
        self.enable_logging = enable_logging
        
        # Initialize CLIP model
        try:
            # Set device (GPU or CPU)
            self.device = "cuda" if torch.cuda.is_available() and enable_gpu else "cpu"
            
            # Load CLIP model
            if model_name not in self.AVAILABLE_MODELS:
                raise ValueError(f"Model {model_name} not supported. Available models: {list(self.AVAILABLE_MODELS.keys())}")
            
            self.model, self.preprocess = clip.load(self.AVAILABLE_MODELS[model_name], device=self.device)
            
            if self.enable_logging:
                logger.info(f"CLIP model {model_name} loaded on {self.device}")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Failed to load CLIP model: {str(e)}")
            raise
    
    @lru_cache(maxsize=100)
    def _get_text_embedding(self, text: str) -> torch.Tensor:
        """Get CLIP embedding for text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            torch.Tensor: Text embedding
        """
        with torch.no_grad():
            text_tokens = clip.tokenize([text]).to(self.device)
            text_embedding = self.model.encode_text(text_tokens)
            # Normalize embedding
            text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
        return text_embedding
    
    def _get_image_embedding(self, image_path: str) -> torch.Tensor:
        """Get CLIP embedding for image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            torch.Tensor: Image embedding
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
            # Downscale very large images to reduce VRAM and speed up inference
            max_side = 1024
            if max(image.size) > max_side:
                ratio = max_side / float(max(image.size))
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size)
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Get image embedding
            with torch.no_grad():
                image_embedding = self.model.encode_image(image_input)
                # Normalize embedding
                image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)
            
            return image_embedding
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error getting image embedding: {str(e)}")
            raise
    
    def _calculate_similarity(self, image_embedding: torch.Tensor, text_embedding: torch.Tensor) -> float:
        """Calculate cosine similarity between image and text embeddings.
        
        Args:
            image_embedding: Image embedding tensor
            text_embedding: Text embedding tensor
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        # Calculate cosine similarity
        similarity = torch.nn.functional.cosine_similarity(image_embedding, text_embedding).item()
        return similarity
    
    def _calculate_confidence_interval(self, similarity: float, sample_size: int = 10) -> Tuple[float, float]:
        """Calculate confidence interval for similarity score.
        
        Args:
            similarity: Similarity score
            sample_size: Effective sample size for confidence calculation
            
        Returns:
            Tuple[float, float]: Lower and upper bounds of 95% confidence interval
        """
        # Standard error calculation (simplified approach)
        std_error = np.sqrt(max(1e-9, (1 - similarity**2)) / max(2, (sample_size - 2)))
        
        # 95% confidence interval (using z=1.96 for 95% CI)
        lower_bound = max(0.0, similarity - 1.96 * std_error)
        upper_bound = min(1.0, similarity + 1.96 * std_error)
        
        return (lower_bound, upper_bound)
    
    def _detect_mismatches(self, image_path: str, text: str) -> Dict:
        """Detect specific mismatches between image and text.
        
        Args:
            image_path: Path to the image file
            text: Text description
            
        Returns:
            Dict: Mismatch detection results
        """
        result = {
            "mismatches": [],
            "attribute_scores": {}
        }
        
        # Get image embedding (cached by path + mtime)
        try:
            mtime = os.path.getmtime(image_path)
        except Exception:
            mtime = 0.0
        # simple manual cache using lru_cache on a wrapper
        if not hasattr(self, "_image_embed_cache"):
            self._image_embed_cache = {}
        cache_key = (image_path, mtime)
        if cache_key in self._image_embed_cache:
            image_embedding = self._image_embed_cache[cache_key]
        else:
            image_embedding = self._get_image_embedding(image_path)
            # keep small cache
            if len(self._image_embed_cache) > 256:
                self._image_embed_cache.pop(next(iter(self._image_embed_cache)))
            self._image_embed_cache[cache_key] = image_embedding
        
        # Check each attribute category
        for category, attributes in self.ATTRIBUTE_CATEGORIES.items():
            category_scores = {}
            
            # Get embeddings and similarities for each attribute
            for attribute in attributes:
                # Create a simple test phrase
                test_text = f"a {attribute} item" if category != 'brand' else f"a {attribute} product"
                
                # Get text embedding
                text_embedding = self._get_text_embedding(test_text)
                
                # Calculate similarity
                similarity = self._calculate_similarity(image_embedding, text_embedding)
                category_scores[attribute] = similarity
            
            # Find the attribute with highest similarity in this category
            best_attribute = max(category_scores.items(), key=lambda x: x[1])
            result["attribute_scores"][category] = {
                "best_match": best_attribute[0],
                "score": best_attribute[1],
                "all_scores": category_scores
            }
            
            # Check if this attribute is mentioned in the text but doesn't match the image
            for attribute in attributes:
                if attribute.lower() in text.lower() and attribute != best_attribute[0] and best_attribute[1] > 0.3:
                    result["mismatches"].append({
                        "category": category,
                        "mentioned": attribute,
                        "likely_actual": best_attribute[0],
                        "confidence": best_attribute[1]
                    })
        
        return result
    
    def _generate_alternative_suggestions(self, text: str, mismatches: List[Dict]) -> List[str]:
        """Generate alternative description suggestions based on detected mismatches.
        
        Args:
            text: Original text description
            mismatches: List of detected mismatches
            
        Returns:
            List[str]: Alternative description suggestions
        """
        suggestions = []
        
        if not mismatches:
            return suggestions
        
        # Create a corrected version of the text
        corrected_text = text
        for mismatch in mismatches:
            mentioned = mismatch["mentioned"]
            likely_actual = mismatch["likely_actual"]
            category = mismatch["category"]
            
            # Replace the mentioned attribute with the likely actual one
            corrected_text = corrected_text.replace(mentioned, likely_actual)
            
            # Add specific suggestion
            suggestions.append(f"Consider changing '{mentioned}' to '{likely_actual}' for better {category} match")
        
        # Add the fully corrected text as a suggestion
        if corrected_text != text:
            suggestions.append(f"Suggested description: {corrected_text}")
        
        return suggestions
    
    def validate_file(self, image_path: str) -> Dict:
        """Validate image file format and size.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict containing file validation results
        """
        result = {
            "valid": False,
            "format": "",
            "size": 0,
            "message": ""
        }
        
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                result["message"] = "File does not exist"
                return result
            
            # Get file extension
            _, ext = os.path.splitext(image_path.lower())
            result["format"] = ext
            
            # Check if format is supported
            if ext not in self.SUPPORTED_FORMATS:
                result["message"] = f"Unsupported image format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                return result
            
            # Check file size
            file_size = os.path.getsize(image_path)
            result["size"] = file_size
            
            if file_size > self.MAX_FILE_SIZE:
                result["message"] = f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
                return result
            
            # All checks passed
            result["valid"] = True
            result["message"] = "File validation passed"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during file validation: {str(e)}")
            result["message"] = f"Error during file validation: {str(e)}"
        
        return result
    
    def validate_alignment(self, image_path: str, text: str) -> Dict:
        """Validate semantic alignment between an image and text description.
        
        Args:
            image_path: Path to the image file
            text: Text description to validate against the image
            
        Returns:
            Dict containing validation results with the following structure:
            {
                "valid": bool,  # Overall validity of the alignment
                "file_validation": {  # File validation results
                    "valid": bool,
                    "format": str,
                    "size": int,
                    "message": str
                },
                "alignment": {  # Alignment results
                    "valid": bool,
                    "similarity": float,
                    "threshold": float,
                    "confidence_interval": [float, float],
                    "message": str
                },
                "mismatch_detection": {  # Mismatch detection results
                    "mismatches": List[Dict],
                    "attribute_scores": Dict
                },
                "suggestions": List[str],  # Alternative description suggestions
                "processing_time": float,  # Total processing time in seconds
                "message": str  # Overall validation message
            }
        """
        start_time = time.time()
        
        # Initialize result structure
        result = {
            "valid": False,
            "file_validation": {},
            "alignment": {
                "valid": False,
                "similarity": 0.0,
                "threshold": self.similarity_threshold,
                "confidence_interval": [0.0, 0.0],
                "message": ""
            },
            "mismatch_detection": {
                "mismatches": [],
                "attribute_scores": {}
            },
            "suggestions": [],
            "processing_time": 0,
            "message": ""
        }
        
        try:
            # Step 1: Validate file format and size
            file_validation = self.validate_file(image_path)
            result["file_validation"] = file_validation
            
            if not file_validation["valid"]:
                result["message"] = "File validation failed: " + file_validation["message"]
                result["processing_time"] = time.time() - start_time
                return result
            
            # Step 2: Get embeddings
            image_embedding = self._get_image_embedding(image_path)
            text_embedding = self._get_text_embedding(text)
            
            # Step 3: Calculate similarity
            similarity = self._calculate_similarity(image_embedding, text_embedding)
            ci_low, ci_high = self._calculate_confidence_interval(similarity)
            
            # Update alignment results
            result["alignment"]["similarity"] = similarity
            result["alignment"]["threshold"] = self.similarity_threshold
            result["alignment"]["confidence_interval"] = [ci_low, ci_high]
            # Significance of decision boundary
            if ci_low >= self.similarity_threshold:
                result["alignment"]["significance"] = "positive"
            elif ci_high < self.similarity_threshold:
                result["alignment"]["significance"] = "negative"
            else:
                result["alignment"]["significance"] = "borderline"
            result["alignment"]["similarity"] = similarity
            result["alignment"]["confidence_interval"] = confidence_interval
            result["alignment"]["valid"] = similarity >= self.similarity_threshold
            
            if result["alignment"]["valid"]:
                result["alignment"]["message"] = "Image and text are semantically aligned"
            else:
                result["alignment"]["message"] = f"Image and text are not well aligned (similarity: {similarity:.2f}, threshold: {self.similarity_threshold})"
            
            # Step 4: Detect mismatches
            mismatch_detection = self._detect_mismatches(image_path, text)
            result["mismatch_detection"] = mismatch_detection
            
            # Step 5: Generate suggestions
            suggestions = self._generate_alternative_suggestions(text, mismatch_detection["mismatches"])
            result["suggestions"] = suggestions
            
            # Determine overall validity
            result["valid"] = result["alignment"]["valid"]
            
            if result["valid"]:
                result["message"] = "Image and text are semantically consistent"
            else:
                result["message"] = f"Image and text are not semantically consistent (similarity: {similarity:.2f})"
                if mismatch_detection["mismatches"]:
                    mismatch_categories = [m["category"] for m in mismatch_detection["mismatches"]]
                    result["message"] += f". Potential mismatches in: {', '.join(mismatch_categories)}"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during alignment validation: {str(e)}")
            result["message"] = f"Error during validation: {str(e)}"
        
        # Calculate total processing time
        result["processing_time"] = time.time() - start_time
        
        return result
    
    def batch_validate(self, image_text_pairs: List[Dict[str, str]]) -> List[Dict]:
        """Validate multiple image-text pairs in batch mode.
        
        Args:
            image_text_pairs: List of dictionaries with 'image' and 'text' keys
            
        Returns:
            List[Dict]: List of validation results for each pair
        """
        results = []
        
        for i, pair in enumerate(image_text_pairs):
            if self.enable_logging:
                logger.info(f"Processing pair {i+1}/{len(image_text_pairs)}")
            
            # Validate individual pair
            try:
                result = self.validate_alignment(pair["image"], pair["text"])
                results.append(result)
            except Exception as e:
                if self.enable_logging:
                    logger.error(f"Error processing pair {i+1}: {str(e)}")
                
                # Add error result
                results.append({
                    "valid": False,
                    "message": f"Error processing pair: {str(e)}",
                    "processing_time": 0
                })
        
        return results
    
    def multi_scale_analysis(self, image_path: str, text: str, scales: List[int] = [10, 20, 50, 100]) -> Dict:
        """Perform multi-scale analysis for different text lengths.
        
        Args:
            image_path: Path to the image file
            text: Full text description
            scales: List of word counts to analyze (default: [10, 20, 50, 100])
            
        Returns:
            Dict: Multi-scale analysis results
        """
        result = {
            "full_text": {
                "text": text,
                "word_count": len(text.split()),
                "similarity": 0.0
            },
            "scales": []
        }
        
        try:
            # Get image embedding
            image_embedding = self._get_image_embedding(image_path)
            
            # Analyze full text
            text_embedding = self._get_text_embedding(text)
            similarity = self._calculate_similarity(image_embedding, text_embedding)
            result["full_text"]["similarity"] = similarity
            
            # Analyze at different scales
            words = text.split()
            for scale in scales:
                if scale >= len(words):
                    continue
                
                # Get truncated text
                truncated_text = " ".join(words[:scale])
                
                # Get embedding and calculate similarity
                trunc_embedding = self._get_text_embedding(truncated_text)
                trunc_similarity = self._calculate_similarity(image_embedding, trunc_embedding)
                
                # Add to results
                result["scales"].append({
                    "word_count": scale,
                    "text": truncated_text,
                    "similarity": trunc_similarity
                })
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during multi-scale analysis: {str(e)}")
        
        return result
