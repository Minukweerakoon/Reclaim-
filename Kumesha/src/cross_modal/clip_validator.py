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

    # Canonicalization maps keep mismatch checks stable across synonyms/spelling.
    COLOR_ALIASES = {
        'grey': 'gray',
        'charcoal': 'gray',
        'navy': 'blue',
        'tan': 'brown',
        'beige': 'brown',
        'maroon': 'red',
        'burgundy': 'red',
    }

    ITEM_ALIASES = {
        'cellphone': 'phone',
        'mobile': 'phone',
        'smartphone': 'phone',
        'billfold': 'wallet',
        'cardholder': 'wallet',
        'purse': 'wallet',
        'handbag': 'bag',
        'satchel': 'bag',
        'rucksack': 'backpack',
        'earphones': 'earbuds',
    }

    BRAND_ALIASES = {
        'lv': 'louis vuitton',
        'louis vuitton': 'louis vuitton',
        'samsung': 'samsung',
        'gucci': 'gucci',
        'prada': 'prada',
        'apple': 'apple',
        'nike': 'nike',
        'adidas': 'adidas',
        'dell': 'dell',
        'hp': 'hp',
        'lenovo': 'lenovo',
        'sony': 'sony',
        'rolex': 'rolex',
        'casio': 'casio',
        'asus': 'asus',
        'acer': 'acer',
        'logitech': 'logitech',
        'logi': 'logitech',
        'razer': 'razer',
        'corsair': 'corsair',
        'steelseries': 'steelseries',
        'hyperx': 'hyperx',
        'thinkpad': 'lenovo',
    }

    # Higher-risk items should use stricter image-text alignment by default.
    ITEM_THRESHOLD_OVERRIDES = {
        'phone': 0.62,      # Lowered from 0.68
        'laptop': 0.60,     # Lowered from 0.66
        'wallet': 0.60,     # Lowered from 0.66
        'watch': 0.60,      # Lowered from 0.66
        'card': 0.60,       # Lowered from 0.66
        'keys': 0.58,       # Lowered from 0.64
    }
    

    
    def __init__(self, 
                 similarity_threshold: float = 0.30,  # Lowered to 30% for generic casual descriptions
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
        # Calculate raw cosine similarity (range: [-1, 1])
        raw_similarity = torch.nn.functional.cosine_similarity(image_embedding, text_embedding).item()
        
        # Empirical PyTorch CLIP calibration:
        # Raw cosine similarities typically range from ~0.15 (mismatch) to ~0.35 (strong match).
        # We linearly scale this range to a clean 0% to 100% confidence score.
        min_expected = 0.15
        max_expected = 0.35
        
        normalized_similarity = (raw_similarity - min_expected) / (max_expected - min_expected)
        
        # Clamp perfectly between 0.0 and 1.0
        return max(0.0, min(1.0, normalized_similarity))

    @staticmethod
    def _normalize_token(value: str) -> str:
        return " ".join((value or '').lower().strip().split())

    def _canonicalize_item(self, value: str) -> str:
        normalized = self._normalize_token(value)
        return self.ITEM_ALIASES.get(normalized, normalized)

    def _canonicalize_color(self, value: str) -> str:
        normalized = self._normalize_token(value)
        return self.COLOR_ALIASES.get(normalized, normalized)

    def _canonicalize_brand(self, value: str) -> str:
        normalized = self._normalize_token(value)
        return self.BRAND_ALIASES.get(normalized, normalized)

    def _extract_mentions(self, text: str, labels: List[str], normalize_kind: str = "item") -> List[str]:
        normalized_text = f" {self._normalize_token(text)} "
        mentions: List[str] = []
        for label in labels:
            token = self._normalize_token(label)
            if f" {token} " in normalized_text:
                if normalize_kind == "color":
                    mentions.append(self._canonicalize_color(token))
                elif normalize_kind == "brand":
                    mentions.append(self._canonicalize_brand(token))
                else:
                    mentions.append(self._canonicalize_item(token))

        # De-duplicate while preserving order
        unique: List[str] = []
        for mention in mentions:
            if mention and mention not in unique:
                unique.append(mention)
        return unique

    @staticmethod
    def _dedupe(values: List[str]) -> List[str]:
        unique: List[str] = []
        for value in values:
            if value and value not in unique:
                unique.append(value)
        return unique
    

    

    

    

    
    def validate_image_text_alignment(self, image_path: str, text: str, analysis_text: Optional[str] = None) -> Dict:
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
            
            # ── Adaptive threshold by item type ────────────────────────────────
            # CLIP scores are systematically lower for peripherals (keyboards, mice,
            # headphones, chargers) because they are less-common in CLIP's training data.
            # Use a lower threshold so they are not falsely flagged as mismatches.
            PERIPHERAL_KEYWORDS = {
                "keyboard", "mouse", "charger", "cable", "remote", "earbuds",
                "headphones", "headset", "usb", "power bank", "hard drive",
                "usb drive", "adapter", "hub", "dock", "speaker"
            }
            analysis_input = analysis_text if analysis_text else text
            text_lower_check = analysis_input.lower()
            is_peripheral = any(kw in text_lower_check for kw in PERIPHERAL_KEYWORDS)
            effective_threshold = 0.30 if is_peripheral else self.similarity_threshold

            result["threshold"] = effective_threshold
            result["valid"] = similarity >= effective_threshold
            result["effective_similarity"] = round(similarity, 3)
            result["mismatch_penalty"] = 0.0
            if is_peripheral:
                logger.info(
                    f"[CLIP] Peripheral item detected — using relaxed threshold "
                    f"{effective_threshold} (raw sim: {similarity:.3f})"
                )

            # Lightweight attribute-level diagnostics using CLIP zero-shot prompts
            try:
                item_labels = [
                    "phone","smartphone","cellphone","mobile","wallet","keys","bag","backpack",
                    "laptop","umbrella","watch","glasses","headphones","earbuds","camera","book",
                    "jacket","purse","card","billfold","purse","handbag",
                    # Peripherals and accessories (CLIP scores lower for these)
                    "keyboard","mouse","charger","cable","remote","tablet","speaker",
                    "power bank","hard drive","usb drive","pen","pencil case"
                ]
                color_labels = [
                    "black","white","red","blue","green","yellow","brown","gray","purple",
                    "orange","pink","silver","gold"
                ]
                brand_labels = [
                    "apple", "samsung", "dell", "asus", "hp", "lenovo", "acer", "sony",
                    "nike", "adidas", "puma", "reebok", "gucci", "prada", "louis vuitton",
                    "rolex", "casio", "michael kors", "coach", "chanel", "hermes",
                    "logitech", "razer", "corsair", "steelseries", "hyperx", "thinkpad"
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
                brand_prompts = [f"{b} brand" for b in brand_labels]
            
                
                #items colours and brands
                top_items = _score_prompts(item_prompts)[:3]
                top_colors = _score_prompts(color_prompts)[:3]
                top_brands = _score_prompts(brand_prompts)[:3]

                # Extract tokens from user text for comparison.
                mention_source = analysis_input.lower()
                mentioned_items = self._extract_mentions(mention_source, item_labels, normalize_kind="item")
                mentioned_colors = self._extract_mentions(mention_source, color_labels, normalize_kind="color")
                mentioned_brands = self._extract_mentions(mention_source, brand_labels, normalize_kind="brand")

                # Log extracted entities for debugging
                if self.enable_logging:
                    logger.info(f"[Entity Extraction] Text: '{mention_source}'")
                    logger.info(f"[Entity Extraction] Items: {mentioned_items}")
                    logger.info(f"[Entity Extraction] Colors: {mentioned_colors}")
                    logger.info(f"[Entity Extraction] Brands: {mentioned_brands}")

                # Raise threshold for specific high-risk items when explicitly mentioned.
                mentioned_thresholds = [
                    self.ITEM_THRESHOLD_OVERRIDES[item]
                    for item in mentioned_items
                    if item in self.ITEM_THRESHOLD_OVERRIDES
                ]
                if mentioned_thresholds:
                    effective_threshold = max(effective_threshold, max(mentioned_thresholds))
                    result["threshold"] = effective_threshold

                # Attribute scores
                result["mismatch_detection"]["attribute_scores"] = {
                    "predicted_items": top_items,
                    "predicted_colors": top_colors,
                    "predicted_brands": top_brands,
                    "mentioned_items": mentioned_items,
                    "mentioned_colors": mentioned_colors,
                    "mentioned_brands": mentioned_brands,
                }

                # Basic mismatch detection and suggestions
                mismatches: List[Dict[str, Any]] = []
                item_mismatch = False
                color_mismatch = False
                brand_mismatch = False

                top_item_labels = self._dedupe([
                    self._canonicalize_item(t[0].split(" ")[-1]) for t in top_items
                ])
                top_color_labels = self._dedupe([
                    self._canonicalize_color(t[0].split(" ")[0]) for t in top_colors
                ])
                top_brand_labels = self._dedupe([
                    self._canonicalize_brand(t[0].replace(" brand", "")) for t in top_brands
                ])

                # Log detected attributes for debugging
                if self.enable_logging:
                    logger.info(f"[Attribute Detection] Top items: {top_item_labels}")
                    logger.info(f"[Attribute Detection] Top colors: {top_color_labels}")
                    logger.info(f"[Attribute Detection] Top brands: {top_brand_labels}")

                # Check for explicit contradictions.
                if mentioned_items:
                    if not set(mentioned_items) & set(top_item_labels):
                        mismatches.append({"type": "item", "message": "Item type in text not prominent in image"})
                        item_mismatch = True
                        if self.enable_logging:
                            logger.info(f"[Mismatch] Item mismatch: mentioned {mentioned_items} vs detected {top_item_labels}")
                if mentioned_colors:
                    if not set(mentioned_colors) & set(top_color_labels):
                        mismatches.append({"type": "color", "message": "Color in text not prominent in image"})
                        color_mismatch = True
                        if self.enable_logging:
                            logger.info(f"[Mismatch] Color mismatch: mentioned {mentioned_colors} vs detected {top_color_labels}")
                if mentioned_brands:
                    if not set(mentioned_brands) & set(top_brand_labels):
                        mismatches.append({"type": "brand", "message": "Brand in text not prominent in image"})
                        brand_mismatch = True
                        if self.enable_logging:
                            logger.info(f"[Mismatch] Brand mismatch: mentioned {mentioned_brands} vs detected {top_brand_labels}")
                result["mismatch_detection"]["mismatches"] = mismatches

                # Penalize semantic alignment when explicit contradictions are found.
                mismatch_penalty = 0.0
                if item_mismatch:
                    mismatch_penalty += 0.22
                if color_mismatch:
                    mismatch_penalty += 0.10
                if brand_mismatch:
                    mismatch_penalty += 0.16
                mismatch_penalty = min(0.42, mismatch_penalty)
                effective_similarity = max(0.0, similarity - mismatch_penalty)
                result["mismatch_penalty"] = round(mismatch_penalty, 3)
                result["effective_similarity"] = round(effective_similarity, 3)

                # Log penalty calculation
                if self.enable_logging and mismatch_penalty > 0:
                    logger.info(f"[Penalty] Item: {0.22 if item_mismatch else 0:.2f}, Color: {0.10 if color_mismatch else 0:.2f}, Brand: {0.16 if brand_mismatch else 0:.2f} | Total: {mismatch_penalty:.3f}")

                # Determine validity using penalized similarity and adaptive threshold.
                result["valid"] = effective_similarity >= effective_threshold

                # Suggestions
                if not result["valid"]:
                    if top_items and (not mentioned_items or item_mismatch):
                        result["suggestions"].append(
                            f"Consider describing it as '{top_items[0][0].replace('a photo of a ','')}'."
                        )
                    if top_colors and (not mentioned_colors or color_mismatch):
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
                
                if mentioned_brands and top_brands:
                    top_brand_name = top_brands[0][0].split(' ')[0]
                    if all(mb not in top_brand_name for mb in mentioned_brands):
                        explanations.append(f"Conflict detected: Text mentions '{mentioned_brands[0]}' but image appears '{top_brand_name}'")

                if mentioned_items and top_items:
                    top_item_name = top_items[0][0].replace('a photo of a ', '')
                    if all(mi not in top_item_name for mi in mentioned_items):
                         explanations.append(f"Conflict detected: Text mentions '{mentioned_items[0]}' but image looks like '{top_item_name}'")

                if result.get("mismatch_penalty", 0) > 0:
                    explanations.append(f"Mismatch penalty applied: -{int(result['mismatch_penalty'] * 100)} points")

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
    
