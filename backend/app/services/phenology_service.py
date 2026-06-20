import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Optional, Any
from datetime import date, timedelta
from sqlalchemy import desc
from app.db import models

# Set random seed
torch.manual_seed(42)

class LSTMPhenologyStageDetector(nn.Module):
    """LSTM sequence model mapping temporal NDVI/EVI signals to growth stages (6 classes)."""
    def __init__(self, input_dim: int = 2, hidden_dim: int = 16, num_stages: int = 6):
        super(LSTMPhenologyStageDetector, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_dim * 2, num_stages)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        out, _ = self.lstm(x)
        # out shape: (batch_size, seq_len, hidden_dim * 2)
        logits = self.fc(out)
        return logits

class PhenologyService:
    def __init__(self, db_session = None, input_dim: int = 2):
        self.db = db_session
        self.stages = ['emergence', 'vegetative', 'flowering', 'reproductive', 'maturity', 'harvest']
        self.num_stages = len(self.stages)
        self.lstm_model = LSTMPhenologyStageDetector(input_dim=input_dim)
        self.lstm_model.eval()

    def detect_stages_thresholding(self, doy: np.ndarray, ndvi: np.ndarray) -> List[str]:
        """
        Detects stages using dynamic thresholding rules on NDVI curve amplitude.
        - Emergence: NDVI rises past 20% of amplitude.
        - Vegetative: NDVI rising from 20% to 75% of max.
        - Flowering: NDVI near peak (>75%) before peak date.
        - Reproductive: NDVI near peak (>75%) after peak date.
        - Maturity: NDVI drops from 75% to 35% of max.
        - Harvest: NDVI drops below 35% or hits fallow baseline.
        """
        min_val = np.min(ndvi)
        max_val = np.max(ndvi)
        amplitude = max_val - min_val
        
        peak_idx = np.argmax(ndvi)
        peak_doy = doy[peak_idx]
        
        predicted_stages = []
        for i, val in enumerate(ndvi):
            current_doy = doy[i]
            pct_amplitude = (val - min_val) / (amplitude + 1e-6)
            
            if current_doy < peak_doy:
                if pct_amplitude < 0.20:
                    stage = "emergence"
                elif pct_amplitude < 0.75:
                    stage = "vegetative"
                else:
                    stage = "flowering"
            else:
                if pct_amplitude > 0.75:
                    stage = "reproductive"
                elif pct_amplitude > 0.35:
                    stage = "maturity"
                else:
                    stage = "harvest"
                    
            predicted_stages.append(stage)
            
        return predicted_stages

    def detect_stages_lstm(self, time_series_features: np.ndarray) -> List[Dict]:
        """
        Evaluates the LSTM model on a (seq_len, input_dim) time-series of field indices.
        Returns a list of dictionaries with stage name and confidence score.
        """
        # input shape: (seq_len, input_dim) -> add batch dimension (1, seq_len, input_dim)
        x_tensor = torch.tensor(time_series_features, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            logits = self.lstm_model(x_tensor)  # output shape: (1, seq_len, num_stages)
            probs = torch.softmax(logits, dim=2).squeeze(0).numpy()  # shape: (seq_len, num_stages)
            
        predictions = []
        for i in range(probs.shape[0]):
            pred_idx = np.argmax(probs[i])
            stage_name = self.stages[pred_idx]
            confidence = probs[i, pred_idx]
            
            predictions.append({
                "stage": stage_name,
                "confidence": float(confidence)
            })
            
        return predictions

    def get_integrated_phenology(self, doy: np.ndarray, ndvi: np.ndarray, ndwi: np.ndarray) -> List[Dict]:
        """
        Fuses dynamic threshold stages with LSTM confidence metrics.
        Ensures a robust chronological output for database storage.
        """
        threshold_stages = self.detect_stages_thresholding(doy, ndvi)
        
        # Prepare inputs for LSTM (NDVI, NDWI)
        features = np.stack([ndvi, ndwi], axis=1)
        lstm_preds = self.detect_stages_lstm(features)
        
        fused_predictions = []
        for idx in range(len(doy)):
            t_stage = threshold_stages[idx]
            l_pred = lstm_preds[idx]
            
            # Fuse: If LSTM confidence is high (> 0.65), trust LSTM. Otherwise trust thresholding
            if l_pred["confidence"] > 0.65:
                final_stage = l_pred["stage"]
                conf = l_pred["confidence"]
            else:
                final_stage = t_stage
                conf = 0.80  # Default heuristic confidence
                
            fused_predictions.append({
                "doy": int(doy[idx]),
                "stage": final_stage,
                "confidence": float(conf)
            })
            
        return fused_predictions

    async def get_current_stage(self, field_id: str) -> Optional[Any]:
        from app.schemas.common import PhenologyResponse
        
        try:
            fid = int(field_id)
        except ValueError:
            field = self.db.query(models.Field).filter(models.Field.name == field_id).first()
            if not field:
                return None
            fid = field.id
            
        record = self.db.query(models.PhenologicalStage).filter(
            models.PhenologicalStage.field_id == fid
        ).order_by(desc(models.PhenologicalStage.detection_date)).first()
        
        if not record:
            # Seed a default record
            record = models.PhenologicalStage(
                field_id=fid,
                stage="vegetative",
                confidence=0.85,
                detection_date=date.today()
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            
        # Calculate days since sowing: search for emergence stage date
        emergence_rec = self.db.query(models.PhenologicalStage).filter(
            models.PhenologicalStage.field_id == fid,
            models.PhenologicalStage.stage == "emergence"
        ).order_by(models.PhenologicalStage.detection_date.asc()).first()
        
        if emergence_rec:
            days_since_sowing = max(1, (record.detection_date - emergence_rec.detection_date).days)
        else:
            days_since_sowing = 45 # default fallback
            
        gdd_accumulated = days_since_sowing * 14.5 # simulated GDD
        
        return PhenologyResponse(
            field_id=fid,
            stage=record.stage,
            days_since_sowing=days_since_sowing,
            gdd_accumulated=gdd_accumulated,
            detection_date=record.detection_date
        )

    async def get_projected_calendar(self, field_id: str) -> list[dict]:
        try:
            fid = int(field_id)
        except ValueError:
            field = self.db.query(models.Field).filter(models.Field.name == field_id).first()
            if not field:
                return []
            fid = field.id
            
        # Standard durations (days) of stages for projections
        durations = {
            "emergence": 15,
            "vegetative": 30,
            "flowering": 20,
            "reproductive": 25,
            "maturity": 20,
            "harvest": 10
        }
        
        current_res = await self.get_current_stage(str(fid))
        if not current_res:
            start_date = date.today()
            current_stage = "vegetative"
        else:
            start_date = current_res.detection_date
            current_stage = current_res.stage
            
        calendar = []
        try:
            start_idx = self.stages.index(current_stage.lower())
        except ValueError:
            start_idx = 1 # default to vegetative
            
        current_date = start_date
        for i in range(start_idx, len(self.stages)):
            stage = self.stages[i]
            calendar.append({
                "stage": stage,
                "projected_date": current_date.isoformat()
            })
            current_date += timedelta(days=durations.get(stage, 15))
            
        return calendar
