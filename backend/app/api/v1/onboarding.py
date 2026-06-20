from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
from app.dependencies import get_db
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

class OnboardRequest(BaseModel):
    name: str = Field(..., description="Name of the new command area")
    bbox: List[float] = Field(..., description="Bounding box [min_lon, min_lat, max_lon, max_lat]")
    crops: List[str] = Field(default=["wheat", "rice", "cotton"], description="List of crop types to seed")
    capacity_cusec: float = Field(default=1000.0, description="Canal capacity in cusec")
    season_label: str = Field(default="Kharif 2026", description="Season label")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Bhakra Command Area",
                "bbox": [75.02, 30.02, 75.18, 30.18],
                "crops": ["wheat", "rice", "cotton"],
                "capacity_cusec": 1200.0,
                "season_label": "Kharif 2026"
            }
        }

@router.post("/new-command-area")
async def onboard_new_command_area(payload: OnboardRequest, db=Depends(get_db)):
    """
    Onboards a new command area:
    - Registers the CommandArea metadata and boundaries.
    - Triggers synthetic Sentinel-1/Sentinel-2 acquisition timelines.
    - Generates grid-divided fields and seeds multi-sensor historical time-series.
    """
    service = OnboardingService(db)
    try:
        res = await service.onboard_command_area(
            name=payload.name,
            bbox=payload.bbox,
            crops=payload.crops,
            capacity_cusec=payload.capacity_cusec,
            season_label=payload.season_label
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to onboard command area: {str(e)}")
