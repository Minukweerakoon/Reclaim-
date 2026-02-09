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
    # Supported image formats and limits for basic file validation
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    # Available CLIP model variants
    AVAILABLE_MODELS = {
        'ViT-B/32': 'ViT-B/32',
        'ViT-L/14': 'ViT-L/14',
        'RN50': 'RN50'
    }
    

    
    def __init__(self, 
                 similarity_threshold: float = 0.60,  # Lowered to 60% for real-world casual photos
                 model_name: str = 'ViT-B/32',
                 enable_gpu: bool = True,
                 enable_logging: bool = True):
        """Initialize the CLIPValidator with configurable parameters.
        
        Args:
            similarity_threshold: Threshold for cosine similarity (default: 0.70, lowered for Lost & Found)
            model_name: CLIP model variant to use (default: 'ViT-B/32')
            enable_gpu: Whether to use GPU acceleration if available (default: True)
            cache_size: Size of the embedding cache (default: 100)
            enable_logging: Whether to enable logging (default: True)
        """
        self.similarity_threshold = similarity_threshold
        self.model_name = model_name
        self.enable_gpu = enable_gpu
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

    def validate_file(self, image_path: str) -> Dict:
        """Basic image file validation for format and size.

        Returns:
            {
              "valid": bool,
              "format": str,
              "size": int,
              "message": str
            }
        """
        result = {"valid": False, "format": "", "size": 0, "message": ""}
        try:
            if not os.path.exists(image_path):
                result["message"] = "File does not exist"
                return result
            _, ext = os.path.splitext(image_path.lower())
            result["format"] = ext
            if ext not in self.SUPPORTED_FORMATS:
                result["message"] = (
                    f"Unsupported image format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                )
                return result
            file_size = os.path.getsize(image_path)
            result["size"] = file_size
            if file_size > self.MAX_FILE_SIZE:
                result["message"] = (
                    f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
                return result
            result["valid"] = True
            result["message"] = "File validation passed"
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during file validation: {str(e)}")
            result["message"] = f"Error during file validation: {str(e)}"
        return result
    
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
    

    

    

    

    
    def validate_image_text_alignment(self, image_path: str, text: str) -> Dict:
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
            "similarity": 0.0,
            "threshold": self.similarity_threshold,
            "feedback": "",
            "mismatch_detection": {"mismatches": [], "attribute_scores": {}},
            "suggestions": []
        }
        
        try:
            # Step 1: Validate file format and size (internal check, not returned)
            file_validation = self.validate_file(image_path)
            if not file_validation["valid"]:
                result["feedback"] = "File validation failed: " + file_validation["message"]
                return result
            
            # Step 2: Get embeddings
            image_embedding = self._get_image_embedding(image_path)
            text_embedding = self._get_text_embedding(text)
            
            # Step 3: Calculate similarity
            similarity = self._calculate_similarity(image_embedding, text_embedding)
            result["similarity"] = similarity
            
            # Determine validity based on threshold
            result["valid"] = similarity >= self.similarity_threshold

            # Lightweight attribute-level diagnostics using CLIP zero-shot prompts
            try:
                item_labels = [
                    "phone","wallet","keys","bag","backpack","laptop","umbrella","watch",
                    "glasses","headphones","camera","book","jacket","purse","card"
                ]
                color_labels = [
                    "black","white","red","blue","green","yellow","brown","gray","purple",
                    "orange","pink","silver","gold"
                ]
                # Build prompt templates
                def _score_prompts(prompts: List[str]) -> List[Tuple[str, float]]:
                    with torch.no_grad():
                        tokens = clip.tokenize(prompts).to(self.device)
                        txt_emb = self.model.encode_text(tokens)
                        txt_emb = txt_emb / txt_emb.norm(dim=-1, keepdim=True)
                        sims = (image_embedding @ txt_emb.T).squeeze(0)
                        scores = sims.detach().cpu().numpy().tolist()
                    pairs = list(zip(prompts, scores))
                    pairs.sort(key=lambda x: x[1], reverse=True)
                    return pairs

                # Score items and colors
                item_prompts = [f"a photo of a {l}" for l in item_labels]
                color_prompts = [f"{c} color" for c in color_labels]
                top_items = _score_prompts(item_prompts)[:3]
                top_colors = _score_prompts(color_prompts)[:3]

                # Extract tokens from user text for comparison
                text_lower = text.lower()
                mentioned_items = [l for l in item_labels if l in text_lower]
                mentioned_colors = [c for c in color_labels if c in text_lower]

                # Attribute scores
                result["mismatch_detection"]["attribute_scores"] = {
                    "predicted_items": top_items,
                    "predicted_colors": top_colors,
                    "mentioned_items": mentioned_items,
                    "mentioned_colors": mentioned_colors,
                }

                # Basic mismatch detection and suggestions
                mismatches: List[Dict[str, Any]] = []
                if mentioned_items:
                    ti = [t[0].split(" ")[-1] for t in top_items]
                    if all(mi not in ti for mi in mentioned_items):
                        mismatches.append({"type": "item", "message": "Item type in text not prominent in image"})
                if mentioned_colors:
                    tc = [t[0].split(" ")[0] for t in top_colors]
                    if all(mc not in tc for mc in mentioned_colors):
                        mismatches.append({"type": "color", "message": "Color in text not prominent in image"})
                result["mismatch_detection"]["mismatches"] = mismatches

                # Suggestions
                if not result["valid"]:
                    if top_items:
                        result["suggestions"].append(
                            f"Consider describing it as '{top_items[0][0].replace('a photo of a ','')}'."
                        )
                    if top_colors:
                        result["suggestions"].append(
                            f"If applicable, mention color like '{top_colors[0][0].split(' ')[0]}'."
                        )
            except Exception as diag_err:
                if self.enable_logging:
                    logger.warning(f"Diagnostics skipped: {diag_err}")

            # Feedback message
            if result["valid"]:
                result["feedback"] = "Image and text are semantically aligned"
            else:
                # Construct explainable feedback
                explanations = []
                
                # Check for specific mismatches
                if mentioned_colors and top_colors:
                    top_color_name = top_colors[0][0].split(' ')[0]
                    if all(mc not in top_color_name for mc in mentioned_colors):
                        explanations.append(f"Conflict detected: Text mentions '{mentioned_colors[0]}' but image appears '{top_color_name}'")
                
                if mentioned_items and top_items:
                    top_item_name = top_items[0][0].replace('a photo of a ', '')
                    if all(mi not in top_item_name for mi in mentioned_items):
                         explanations.append(f"Conflict detected: Text mentions '{mentioned_items[0]}' but image looks like '{top_item_name}'")

                if explanations:
                    explanation_str = ". ".join(explanations)
                    result["feedback"] = (
                        f"Image and text mismatch (similarity: {similarity:.2f}). {explanation_str}."
                    )
                else:
                    result["feedback"] = (
                        f"Image and text are not well aligned (similarity: {similarity:.2f}, "
                        f"threshold: {self.similarity_threshold})"
                    )
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during alignment validation: {str(e)}")
            result["feedback"] = f"Error during validation: {str(e)}"
        
        return result
    
    def batch_validate(self, pairs: List[Tuple[str, str]]) -> List[Dict]:
        """Validate multiple image-text pairs efficiently.
        
        Args:
            pairs: List of tuples with (image_path, text)
            
        Returns:
            List[Dict]: List of validation results for each pair
        """
        results = []
        
        for i, pair in enumerate(pairs):
            if self.enable_logging:
                logger.info(f"Processing pair {i+1}/{len(pairs)}")
            
            # Validate individual pair
            try:
                result = self.validate_image_text_alignment(pair[0], pair[1])
                results.append(result)
            except Exception as e:
                if self.enable_logging:
                    logger.error(f"Error processing pair {i+1}: {str(e)}")
                
                # Add error result
                results.append({
                    "valid": False,
                    "similarity": 0.0,
                    "threshold": self.similarity_threshold,
                    "feedback": f"Error processing pair: {str(e)}"
                })
        
        return results
    
