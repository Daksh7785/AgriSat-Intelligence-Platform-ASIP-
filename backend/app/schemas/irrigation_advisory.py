from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class IrrigationAdvisoryResponse(BaseModel):
    id: int
    field_id: int
    timestamp: datetime
    recommended_action: str
    recommended_depth_mm: float
    recommended_volume_m3: float
    water_savings_m3: float
    advisory_text: str
    status: str

    class Config:
        from_attributes = True

class CommandAreaAdvisorySummary(BaseModel):
    command_area_id: str
    advisories: List[IrrigationAdvisoryResponse]
    total_water_required_m3: float
    potential_savings_m3: float

    class Config:
        from_attributes = True
