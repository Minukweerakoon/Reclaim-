"""
Semantic Matcher Module for AI-Driven Spatial-Temporal Validation
Uses sentence transformers to find semantically similar items.
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class SemanticMatcher:
    """
    Semantic similarity matcher using sentence transformers.
    Maps unknown items to known categories via embedding similarity.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize semantic matcher.
        
        Args:
            model_name: Pre-trained sentence transformer model
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            self.model = None
        
        # Cache for known item embeddings
        self.known_items_embeddings: Dict[str, np.ndarray] = {}
        self.cache_path = Path("data/semantic_cache.pkl")
        self.cache_path.parent.mkdir(exist_ok=True)
        
        # Load cached embeddings if available
        self._load_cache()
    
    def add_known_item(self, item: str, force_recompute: bool = False) -> None:
        """
        Add a known item and compute its embedding.
        
        Args:
            item: Item name to add
            force_recompute: Force recomputation even if cached
        """
        if not self.model:
            logger.warning("Semantic model not available, skipping")
            return
        
        if item in self.known_items_embeddings and not force_recompute:
            return
        
        try:
            embedding = self.model.encode(item, convert_to_numpy=True)
            self.known_items_embeddings[item] = embedding
            logger.debug(f"Computed embedding for item: {item}")
        except Exception as e:
            logger.error(f"Failed to compute embedding for {item}: {e}")
    
    def add_known_items_batch(self, items: List[str]) -> None:
        """
        Add multiple known items in batch for efficiency.
        
        Args:
            items: List of item names
        """
        if not self.model:
            logger.warning("Semantic model not available, skipping batch add")
            return
        
        # Filter out already cached items
        new_items = [item for item in items if item not in self.known_items_embeddings]
        
        if not new_items:
            logger.debug("All items already cached")
            return
        
        try:
            embeddings = self.model.encode(new_items, convert_to_numpy=True, show_progress_bar=False)
            for item, embedding in zip(new_items, embeddings):
                self.known_items_embeddings[item] = embedding
            
            logger.info(f"Computed embeddings for {len(new_items)} new items")
            self._save_cache()
        except Exception as e:
            logger.error(f"Failed to compute batch embeddings: {e}")
    
    def find_similar_items(
        self, 
        query: str, 
        top_k: int = 3, 
        threshold: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Find semantically similar known items.
        
        Args:
            query: Query item to match
            top_k: Number of top matches to return
            threshold: Minimum similarity score (0-1)
        
        Returns:
            List of (item_name, similarity_score) tuples
        """
        if not self.model or not self.known_items_embeddings:
            logger.warning("Semantic matching not available")
            return []
        
        try:
            # Compute query embedding
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            
            # Compute cosine similarity with all known items
            similarities = []
            for item, item_embedding in self.known_items_embeddings.items():
                # Cosine similarity
                similarity = np.dot(query_embedding, item_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(item_embedding)
                )
                similarities.append((item, float(similarity)))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Filter by threshold and return top_k
            filtered = [(item, score) for item, score in similarities if score >= threshold]
            results = filtered[:top_k]
            
            logger.debug(f"Query '{query}' matched: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar items for '{query}': {e}")
            return []
    
    def get_weighted_category(
        self, 
        query: str, 
        category_map: Dict[str, str],
        threshold: float = 0.6
    ) -> Optional[str]:
        """
        Get category for query based on weighted similarity to known items.
        
        Args:
            query: Query item
            category_map: Mapping from items to categories
            threshold: Minimum confidence threshold
        
        Returns:
            Most likely category or None
        """
        similar_items = self.find_similar_items(query, top_k=5, threshold=0.4)
        
        if not similar_items:
            return None
        
        # Weight categories by similarity scores
        category_scores: Dict[str, float] = {}
        for item, score in similar_items:
            category = category_map.get(item, item)  # Use item itself if no category
            category_scores[category] = category_scores.get(category, 0.0) + score
        
        # Get category with highest weighted score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] / len(similar_items) >= threshold:
                logger.info(f"Matched '{query}' to category '{best_category[0]}' with confidence {best_category[1]:.2f}")
                return best_category[0]
        
        return None
    
    def _save_cache(self) -> None:
        """Save embeddings cache to disk."""
        try:
            with open(self.cache_path, 'wb') as f:
                pickle.dump(self.known_items_embeddings, f)
            logger.debug(f"Saved semantic cache with {len(self.known_items_embeddings)} items")
        except Exception as e:
            logger.warning(f"Failed to save semantic cache: {e}")
    
    def _load_cache(self) -> None:
        """Load embeddings cache from disk."""
        if not self.cache_path.exists():
            return
        
        try:
            with open(self.cache_path, 'rb') as f:
                self.known_items_embeddings = pickle.load(f)
            logger.info(f"Loaded semantic cache with {len(self.known_items_embeddings)} items")
        except Exception as e:
            logger.warning(f"Failed to load semantic cache: {e}")
            self.known_items_embeddings = {}


# Global singleton instance
_semantic_matcher = None


def get_semantic_matcher() -> SemanticMatcher:
    """Get or create the global semantic matcher instance."""
    global _semantic_matcher
    if _semantic_matcher is None:
        _semantic_matcher = SemanticMatcher()
    return _semantic_matcher
