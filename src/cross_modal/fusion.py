"""
Cross-Attention Multimodal Fusion Module
Part of Research-Grade Enhancement (Novel Contribution #2)

This module implements a Cross-Attention mechanism to fuse embeddings from:
1. Text (Query)
2. Image (Key/Value)
3. Voice (Key/Value)

Architecture:
    Input: [Text_Embed, Image_Embed, Voice_Embed]
    Attention: Softmax(Q * K^T / sqrt(d)) * V
    Output: Fused multimodal embedding + match confidence score
"""

import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

logger = logging.getLogger(__name__)

class CrossAttentionFusion(nn.Module):
    """
    PyTorch implementation of Cross-Attention Fusion.
    Allows text queries to 'attend' to relevant visual/audio features.
    """
    
    def __init__(self, embed_dim: int = 512, num_heads: int = 4, dropout: float = 0.1):
        """
        Initialize the fusion model.
        
        Args:
            embed_dim: Dimension of input embeddings (default 512 for CLIP-ViT/B-32)
            num_heads: Number of attention heads
            dropout: Dropout probability
        """
        super().__init__()
        self.embed_dim = embed_dim
        
        # Multi-Head Attention Layer
        # Query = Text, Key/Value = Concatenated [Image, Voice]
        self.multihead_attn = nn.MultiheadAttention(
            embed_dim=embed_dim, 
            num_heads=num_heads, 
            dropout=dropout, 
            batch_first=True
        )
        
        # Feed Forward Network for final scoring
        self.fc_block = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 1),
            nn.Sigmoid()  # Output probability 0-1
        )
        
        # Normalization
        self.layer_norm = nn.LayerNorm(embed_dim)
        
        # Initialize weights (Heuristic initialization for "untrained" mode)
        self._init_weights()

    def _init_weights(self):
        """Initialize weights to act as a reasonable heuristic before training."""
        # Initialize linear layers to pass through signal
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, text_embed: torch.Tensor, image_embed: torch.Tensor, voice_embed: Optional[torch.Tensor] = None):
        """
        Forward pass for fusion.
        
        Args:
            text_embed: (Batch, Dim) - e.g. (1, 512)
            image_embed: (Batch, Dim)
            voice_embed: (Batch, Dim) - Optional
            
        Returns:
            fused_score: (Batch, 1) - Match confidence
        """
        # Ensure dimensions match
        if text_embed.dim() == 1: text_embed = text_embed.unsqueeze(0)
        if image_embed.dim() == 1: image_embed = image_embed.unsqueeze(0)
        
        # Query: Text is the "anchor" we want to verify
        # Shape: (Batch, Seq, Dim) -> (1, 1, 512)
        query = text_embed.unsqueeze(1)
        
        # Key/Value: Concatenate available modalities
        # If voice is None, just use Image. If voice exists, [Image, Voice]
        keys_list = [image_embed.unsqueeze(1)]
        if voice_embed is not None:
            if voice_embed.dim() == 1: voice_embed = voice_embed.unsqueeze(0)
            keys_list.append(voice_embed.unsqueeze(1))
            
        key_value = torch.cat(keys_list, dim=1) # (1, 1 or 2, 512)
        
        # Cross Attention: Text attends to Image/Voice
        attn_output, attn_weights = self.multihead_attn(
            query, 
            key_value, 
            key_value, 
            need_weights=True
        )
        
        # Residual connection + Norm
        fused_embed = self.layer_norm(query + attn_output)
        
        # Final scoring
        score = self.fc_block(fused_embed.squeeze(1))
        
        return score, attn_weights

    @torch.no_grad()
    def fuse_features_heuristic(self, text_embed: np.ndarray, image_embed: np.ndarray, voice_embed: Optional[np.ndarray] = None) -> float:
        """
        Heuristic fusion for inference when model is not fully trained.
        Uses Sim-based logic wrapped in the architecture.
        """
        # Convert numpy to torch
        t_tens = torch.tensor(text_embed, dtype=torch.float32)
        i_tens = torch.tensor(image_embed, dtype=torch.float32)
        v_tens = torch.tensor(voice_embed, dtype=torch.float32) if voice_embed is not None else None
        
        # Calculate Cosine Similarities directly as a baseline
        sim_ti = F.cosine_similarity(t_tens, i_tens, dim=-1).item()
        
        score = sim_ti
        if v_tens is not None:
            sim_tv = F.cosine_similarity(t_tens, v_tens, dim=-1).item()
            # Weighted fusion: Image 60%, Voice 40% (example research heuristic)
            score = 0.6 * sim_ti + 0.4 * sim_tv
            
        return max(0.0, min(1.0, score)) # Clip 0-1
