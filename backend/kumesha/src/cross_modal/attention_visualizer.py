import os
import time
import logging
import cv2
import numpy as np
import torch
import uuid
from PIL import Image
from typing import Dict, List, Optional, Any, Union
import clip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AttentionVisualizer')

class AttentionVisualizer:
    """
    Generates explainable attention maps for Image-Text pairs using CLIP.
    
    Uses an Occlusion Sensitivity approach to visualize which parts of an image
    contribute most to the semantic similarity with the text. This renders a 
    heatmap overlay showing 'where the model is looking'.
    """
    
    def __init__(self, output_dir: str = "uploads/heatmaps"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"AttentionVisualizer initialized on {self.device}, saving to {output_dir}")
        
    def generate_attention_map(self, 
                               image_path: str, 
                               text: str, 
                               clip_model: Any = None, 
                               grid_size: int = 8) -> Dict[str, Any]:
        """
        Generate attention heatmap for a given image and text.
        
        Args:
            image_path: Path to the image file.
            text: Text description.
            clip_model: Loaded CLIP model instance (optional).
            grid_size: Granularity of the heatmap (default 8x8).
            
        Returns:
            Dict containing paths to the heatmap, raw scores, and explanation.
        """
        try:
            # Load basic image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found at {image_path}")
            
            original_image = Image.open(image_path).convert("RGB")
            
            # Helper: Load model if not provided
            if clip_model is None:
                # Fallback to loading a new model if one isn't passed (Slow!)
                model_name = "ViT-B/32"
                logger.info(f"Loading fallback CLIP model {model_name}...")
                model, preprocess = clip.load(model_name, device=self.device)
            else:
                # Handle both raw CLIP model or our CLIPValidator wrapper
                if hasattr(clip_model, 'model'):
                    model = clip_model.model
                    preprocess = clip_model.preprocess
                else:
                    # Raw model passed
                    model = clip_model
                    # Need preprocess. Try standard.
                    try:
                        _, preprocess = clip.load("ViT-B/32", device=self.device)
                    except:
                        # Fallback for mocking/testing
                        logger.warning("Could not load standard preprocess, using identity.")
                        preprocess = lambda x: x

            # Prepare text embedding
            with torch.no_grad():
                text_tokens = clip.tokenize([text]).to(self.device)
                text_features = model.encode_text(text_tokens)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Get Baseline Score
            image_input = preprocess(original_image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                image_features = model.encode_image(image_input)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                baseline_similarity = (image_features @ text_features.T).item()

            # Generate Heatmap via Occlusion
            width, height = original_image.size
            step_x = max(1, width // grid_size)
            step_y = max(1, height // grid_size)
            
            heatmap = np.zeros((grid_size, grid_size))
            
            # Pre-calculate mask color (mean color of image to be neutral)
            img_array = np.array(original_image)
            mean_color = tuple(np.mean(img_array, axis=(0, 1)).astype(int))

            # Occlusion loop
            for i in range(grid_size):
                for j in range(grid_size):
                    # Create occluded image
                    occluded_img = original_image.copy()
                    
                    x1 = i * step_x
                    y1 = j * step_y
                    x2 = (i + 1) * step_x if i < grid_size - 1 else width
                    y2 = (j + 1) * step_y if j < grid_size - 1 else height
                    
                    # Apply mask
                    mask = Image.new('RGB', (x2-x1, y2-y1), color=mean_color)
                    occluded_img.paste(mask, (x1, y1))
                    
                    # Score occluded image
                    occ_input = preprocess(occluded_img).unsqueeze(0).to(self.device)
                    with torch.no_grad():
                        occ_features = model.encode_image(occ_input)
                        occ_features = occ_features / occ_features.norm(dim=-1, keepdim=True)
                        occ_similarity = (occ_features @ text_features.T).item()
                    
                    # Importance = Drop in score
                    importance = max(0, baseline_similarity - occ_similarity)
                    heatmap[j, i] = importance

            # Normalize Heatmap
            if np.max(heatmap) > 0:
                heatmap_norm = heatmap / np.max(heatmap)
            else:
                heatmap_norm = heatmap

            # Upscale heatmap to image size (Bilinear)
            heatmap_resized = cv2.resize(heatmap_norm, (width, height), interpolation=cv2.INTER_LINEAR)
            
            # Apply Color Map (Jet)
            heatmap_uint8 = np.uint8(255 * heatmap_resized)
            heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
            
            # Overlay
            img_bgr = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
            overlay = cv2.addWeighted(img_bgr, 0.6, heatmap_color, 0.4, 0)
            overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            final_img = Image.fromarray(overlay_rgb)
            
            # Save Result
            filename = f"heatmap_{uuid.uuid4().hex}.jpg"
            save_path = os.path.join(self.output_dir, filename)
            final_img.save(save_path)
            
            # Identify Top Regions for Text Explanation
            top_regions = self._identify_top_regions(heatmap, num_regions=3)
            explanation = self._generate_explanation(top_regions, text, baseline_similarity)
            
            return {
                "heatmap_url": f"/uploads/heatmaps/{filename}",
                "attention_scores": heatmap.flatten().tolist(),
                "top_regions": top_regions,
                "explanation": explanation,
                "baseline_similarity": float(baseline_similarity)
            }
            
        except Exception as e:
            logger.error(f"Error generating attention map: {e}")
            return {
                "error": str(e),
                "attention_scores": [],
                "explanation": "Could not generate attention map."
            }

    def _identify_top_regions(self, heatmap: np.ndarray, num_regions: int = 3) -> List[Dict]:
        """
        Identify the grid cells with highest attention.
        Returns coordinates relative to grid (0..1)
        """
        flat_indices = np.argsort(heatmap.ravel())[::-1]
        top_indices = flat_indices[:num_regions]
        
        regions = []
        rows, cols = heatmap.shape
        
        for idx in top_indices:
            r, c = np.unravel_index(idx, (rows, cols))
            score = float(heatmap[r, c])
            if score > 0.0001:  # Filter out trivial info
                regions.append({
                    "grid_x": int(c),
                    "grid_y": int(r),
                    "score": score,
                    "normalized_x": c / cols,
                    "normalized_y": r / rows,
                    "region": self._get_region_name(c/cols, r/rows)
                })
                
        return regions

    def _get_region_name(self, x: float, y: float) -> str:
        h_pos = "left" if x < 0.33 else "right" if x > 0.66 else "center"
        v_pos = "top" if y < 0.33 else "bottom" if y > 0.66 else "center"
        return f"{v_pos}-{h_pos}" if h_pos != "center" or v_pos != "center" else "center"

    def _generate_explanation(self, regions: List[Dict], text: str, similarity: float) -> str:
        """Generate human-readable explanation of the attention."""
        if not regions:
            return "No specific regions of the image strongly increased the match confidence."
            
        main_region = regions[0]["region"]
        
        strength = "strong" if similarity > 0.25 else "weak"
        return (
            f"The model focused primarily on the {main_region} "
            f"part of the image to match the text '{text}'. "
            f"Overall match confidence is {strength}."
        )

# Singleton instance
_attention_visualizer = None

def get_attention_visualizer() -> AttentionVisualizer:
    """Get or create the global AttentionVisualizer instance."""
    global _attention_visualizer
    if _attention_visualizer is None:
        _attention_visualizer = AttentionVisualizer()
    return _attention_visualizer

