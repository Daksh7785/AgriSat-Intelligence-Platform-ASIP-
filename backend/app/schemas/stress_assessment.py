from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FieldStressResponse(BaseModel):
    field_id: int
    timestamp: datetime
    ndvi: Optional[float] = None
    ndwi: Optional[float] = None
    vci: Optional[float] = None
    tci: Optional[float] = None
    vhi: Optional[float] = None
    smi: Optional[float] = None
    stress_level: str
    stress_score: float

    class Config:
        from_attributes = True

class StressMapResponse(BaseModel):
    command_area_id: str
    fields: List[FieldStressResponse]

    class Config:
        from_attributes = True
