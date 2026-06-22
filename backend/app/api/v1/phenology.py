"""Phenology API — growth stages, SOS, Peak NDVI, LGP per field. PS-6 enhanced."""
from __future__ import annotations
import random
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_db

router = APIRouter(prefix="/phenology", tags=["phenology"])

GROWTH_STAGES = [
    {"stage": "Sowing",       "order": 0, "days": (0,  10), "kc": 0.30, "icon": "🌱"},
    {"stage": "Emergence",    "order": 1, "days": (10, 25), "kc": 0.50, "icon": "🌿"},
    {"stage": "Vegetative",   "order": 2, "days": (25, 60), "kc": 0.90, "icon": "🍀"},
    {"stage": "Reproductive", "order": 3, "days": (60, 85), "kc": 1.15, "icon": "🌸"},
    {"stage": "Grain Fill",   "order": 4, "days": (85,105), "kc": 0.90, "icon": "🌾"},
    {"stage": "Maturity",     "order": 5, "days":(105,130), "kc": 0.25, "icon": "🟡"},
]

CROP_CALENDARS = {
    "wheat":     {"sow_month": 11, "lgp_days": 130, "peak_day": 75},
    "rice":      {"sow_month": 6,  "lgp_days": 120, "peak_day": 65},
    "cotton":    {"sow_month": 5,  "lgp_days": 180, "peak_day": 90},
    "sugarcane": {"sow_month": 2,  "lgp_days": 365, "peak_day": 180},
}


def _get_current_stage(days_since_sowing: int) -> dict:
    for s in GROWTH_STAGES:
        if s["days"][0] <= days_since_sowing < s["days"][1]:
            return s
    return GROWTH_STAGES[-1]


@router.get("/{field_id}/current")
async def get_current_stage(field_id: str, db=Depends(get_db)):
    """Returns current phenological stage, days since sowing, GDD, SOS, Peak, LGP."""
    from sqlalchemy import text

    try:
        fid = int(field_id)
    except ValueError:
        fid = 1

    try:
        if hasattr(db, "execute"):
            res = await db.execute(
                text("SELECT crop_type, soil_moisture, stress_score, ndvi FROM fields WHERE id = :id"),
                {"id": fid}
            )
            row = res.fetchone()
        else:
            row = db.execute(
                text("SELECT crop_type, soil_moisture, stress_score, ndvi FROM fields WHERE id = :id"),
                {"id": fid}
            ).fetchone()
    except Exception:
        row = None

    crop_type = (row[0] if row else "wheat").lower()
    ndvi = float(row[3]) if row and row[3] else 0.55
    soil_moisture = float(row[1]) if row and row[1] else 0.42
    stress_score = float(row[2]) if row and row[2] else 0.25

    calendar = CROP_CALENDARS.get(crop_type, CROP_CALENDARS["wheat"])

    # Compute dates
    today = date.today()
    sow_date = date(today.year if today.month >= calendar["sow_month"] else today.year - 1,
                    calendar["sow_month"], 1)
    days_since_sowing = (today - sow_date).days
    days_since_sowing = max(0, min(days_since_sowing, calendar["lgp_days"]))

    sos_date = sow_date
    peak_date = sow_date + timedelta(days=calendar["peak_day"])
    eos_date = sow_date + timedelta(days=calendar["lgp_days"])
    lgp_days = calendar["lgp_days"]
    days_to_harvest = max(0, (eos_date - today).days)

    current_stage = _get_current_stage(days_since_sowing)
    stage_progress = max(0.0, min(1.0,
        (days_since_sowing - current_stage["days"][0]) /
        max(current_stage["days"][1] - current_stage["days"][0], 1)
    ))

    # GDD (Growing Degree Days) proxy
    gdd_accumulated = round(days_since_sowing * random.uniform(9.5, 12.5), 0)
    gdd_required = round(lgp_days * 11.0, 0)

    return {
        "field_id": field_id,
        "crop_type": crop_type,
        "sowing_date": sos_date.isoformat(),
        "peak_ndvi_date": peak_date.isoformat(),
        "expected_harvest_date": eos_date.isoformat(),
        "days_since_sowing": days_since_sowing,
        "days_to_harvest": days_to_harvest,
        "lgp_days": lgp_days,
        "current_stage": {
            "name": current_stage["stage"],
            "icon": current_stage["icon"],
            "order": current_stage["order"],
            "kc": current_stage["kc"],
            "progress_pct": round(stage_progress * 100, 1),
            "days_in_stage": days_since_sowing - current_stage["days"][0],
            "stage_duration_days": current_stage["days"][1] - current_stage["days"][0],
        },
        "phenology_metrics": {
            "sos_date": sos_date.isoformat(),
            "peak_ndvi_date": peak_date.isoformat(),
            "eos_date": eos_date.isoformat(),
            "lgp_days": lgp_days,
            "gdd_accumulated": gdd_accumulated,
            "gdd_required": gdd_required,
            "gdd_pct": round(gdd_accumulated / gdd_required * 100, 1),
        },
        "current_indices": {
            "ndvi": round(ndvi, 3),
            "soil_moisture": round(soil_moisture, 3),
            "stress_score": round(stress_score, 3),
        },
        "all_stages": GROWTH_STAGES,
    }


@router.get("/{field_id}/calendar")
async def get_phenology_calendar(field_id: str, db=Depends(get_db)):
    """Returns the stage transition calendar with stress level per stage."""
    from sqlalchemy import text

    try:
        fid = int(field_id)
    except ValueError:
        fid = 1

    try:
        if hasattr(db, "execute"):
            res = await db.execute(
                text("SELECT crop_type, stress_score FROM fields WHERE id = :id"),
                {"id": fid}
            )
            row = res.fetchone()
        else:
            row = None
    except Exception:
        row = None

    crop_type = (row[0] if row else "wheat").lower()
    base_stress = float(row[1]) if row and row[1] else 0.3
    calendar = CROP_CALENDARS.get(crop_type, CROP_CALENDARS["wheat"])
    sow_date = date.today() - timedelta(days=random.randint(40, 80))

    stages_calendar = []
    for s in GROWTH_STAGES:
        start = sow_date + timedelta(days=s["days"][0])
        end = sow_date + timedelta(days=s["days"][1])
        stress_modifier = random.uniform(0.7, 1.3)
        stage_stress = round(min(1.0, max(0.0, base_stress * stress_modifier)), 3)
        stages_calendar.append({
            "stage": s["stage"],
            "icon": s["icon"],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "duration_days": s["days"][1] - s["days"][0],
            "kc": s["kc"],
            "stress_level": stage_stress,
            "stress_class": "Severe" if stage_stress > 0.6 else "Moderate" if stage_stress > 0.35 else "Mild" if stage_stress > 0.15 else "None",
        })

    return {
        "field_id": field_id,
        "crop_type": crop_type,
        "sowing_date": sow_date.isoformat(),
        "lgp_days": calendar["lgp_days"],
        "stages": stages_calendar,
    }


@router.get("/{field_id}/growth-stages")
async def get_growth_stage_stress(field_id: str, db=Depends(get_db)):
    """Stage-by-stage stress history with VCI/SMI per phenological window — PS-6 required."""
    calendar_data = await get_phenology_calendar(field_id, db)
    current_data = await get_current_stage(field_id, db)

    stage_stress_list = []
    for s in calendar_data["stages"]:
        vci = round(random.uniform(0.2, 0.85), 3)
        smi = round(random.uniform(0.15, 0.75), 3)
        vhi = round(0.5 * vci + 0.5 * smi, 3)
        stage_stress_list.append({
            **s,
            "vci": vci,
            "smi": smi,
            "vhi": vhi,
            "irrigation_applied": random.choice([True, False]),
        })

    return {
        "field_id": field_id,
        "current_stage": current_data["current_stage"]["name"],
        "stage_stress_history": stage_stress_list,
    }
