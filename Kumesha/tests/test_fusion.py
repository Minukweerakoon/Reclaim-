"""
Unit tests for Cross-Attention Fusion Module.
"""
import pytest
import torch
import numpy as np
from src.cross_modal.fusion import CrossAttentionFusion

@pytest.fixture
def fusion_model():
    """Create a fusion model instance."""
    return CrossAttentionFusion(embed_dim=512, num_heads=4)

def test_fusion_forward_pass_shapes(fusion_model):
    """Test standard forward pass tensor shapes."""
    batch_size = 2
    embed_dim = 512
    
    # Create dummy embeddings
    text = torch.randn(batch_size, embed_dim)
    image = torch.randn(batch_size, embed_dim)
    voice = torch.randn(batch_size, embed_dim)
    
    # Forward pass
    score, attn_weights = fusion_model(text, image, voice)
    
    # Check output shapes
    assert score.shape == (batch_size, 1)
    assert attn_weights.shape == (batch_size, 1, 2) # (Batch, Query_Len, Key_Len) matching [Image, Voice]
    
    # Check score range (Sigmoid -> 0-1)
    assert (score >= 0).all() and (score <= 1).all()

def test_fusion_without_voice(fusion_model):
    """Test forward pass works without voice input."""
    text = torch.randn(1, 512)
    image = torch.randn(1, 512)
    
    score, attn_weights = fusion_model(text, image, None)
    
    assert score.shape == (1, 1)
    assert attn_weights.shape == (1, 1, 1) # Just attend to Image

def test_heuristic_fusion(fusion_model):
    """Test the heuristic fallback method."""
    # Perfectly matching vectors (normalized)
    vec = np.ones(512) / np.linalg.norm(np.ones(512))
    
    # Same vector for text and image -> cosine sim should be 1.0
    score = fusion_model.fuse_features_heuristic(vec, vec, None)
    
    assert 0.99 <= score <= 1.0
    
    # Orthogonal vectors -> cosine sim should be 0.0
    vec2 = np.zeros(512)
    vec2[0] = 1.0
    vec3 = np.zeros(512)
    vec3[1] = 1.0
    
    score_ortho = fusion_model.fuse_features_heuristic(vec2, vec3, None)
    assert score_ortho < 0.01

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
