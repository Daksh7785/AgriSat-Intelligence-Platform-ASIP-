"""
SAR-Optical Fusion model using an attention-based fusion mechanism.
"""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


class SAROpticalFusionModel(nn.Module):
    """
    Attention-based SAR + Optical Late Fusion Network.
    
    Processes:
      - Optical feature vector (e.g., NDVI, EVI, NDWI time series)
      - SAR feature vector (e.g., VV, VH, VH/VV ratio time series)
    Fuses them using a cross-attention layer, and maps to classification heads.
    """
    def __init__(
        self,
        optical_dim: int = 16 * 6,  # 16 timesteps x 6 indices
        sar_dim: int = 8 * 3,       # 8 timesteps x 3 channels
        embed_dim: int = 64,
        num_classes: int = 10,
        num_stages: int = 6,
        num_stress_levels: int = 4,
    ):
        super().__init__()
        self.optical_proj = nn.Linear(optical_dim, embed_dim)
        self.sar_proj = nn.Linear(sar_dim, embed_dim)
        
        # Self-attention and cross-attention blocks
        self.query_proj = nn.Linear(embed_dim, embed_dim)
        self.key_proj = nn.Linear(embed_dim, embed_dim)
        self.value_proj = nn.Linear(embed_dim, embed_dim)
        
        self.fusion_fc = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
        )
        
        # Multi-task heads
        self.crop_type_head = nn.Linear(embed_dim, num_classes)
        self.phenology_head = nn.Linear(embed_dim, num_stages)
        self.stress_head = nn.Linear(embed_dim, num_stress_levels)

    def forward(self, optical_x: torch.Tensor, sar_x: torch.Tensor) -> dict[str, torch.Tensor]:
        """
        Args:
            optical_x: Tensor of shape [batch_size, optical_dim]
            sar_x: Tensor of shape [batch_size, sar_dim]
        Returns:
            Dict of head logits: crop_type, phenology_stage, moisture_stress
        """
        opt_embed = F.relu(self.optical_proj(optical_x))  # [B, embed_dim]
        sar_embed = F.relu(self.sar_proj(sar_x))        # [B, embed_dim]
        
        # Compute simplified dot-product attention from optical to SAR
        # Q: optical, K: SAR, V: SAR
        q = self.query_proj(opt_embed).unsqueeze(1)  # [B, 1, embed_dim]
        k = self.key_proj(sar_embed).unsqueeze(2)    # [B, embed_dim, 1]
        v = self.value_proj(sar_embed)              # [B, embed_dim]
        
        attn_weights = F.softmax(torch.bmm(q, k).squeeze(2), dim=-1)  # [B, 1]
        attn_out = attn_weights * v  # [B, embed_dim]
        
        # Concat original optical embed with attended SAR embed
        fused = torch.cat([opt_embed, attn_out], dim=-1)  # [B, embed_dim * 2]
        fused_features = self.fusion_fc(fused)           # [B, embed_dim]
        
        return {
            "crop_type": self.crop_type_head(fused_features),
            "phenology_stage": self.phenology_head(fused_features),
            "moisture_stress": self.stress_head(fused_features),
        }
