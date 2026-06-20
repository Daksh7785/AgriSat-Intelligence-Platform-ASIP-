from pydantic import BaseModel
from typing import Optional
from datetime import date

class PhenologyResponse(BaseModel):
    field_id: int
    stage: str
    days_since_sowing: int
    gdd_accumulated: float
    detection_date: date

    class Config:
        from_attributes = True


class FeatureAttribution(BaseModel):
    feature: str
    shap_value: float
    raw_value: float


class PixelExplanationResponse(BaseModel):
    predicted_class: str
    confidence: float
    top_features: list[FeatureAttribution]
    natural_language_summary: str

    class Config:
        from_attributes = True

