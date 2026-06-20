# 📡 Kisan Drishti — Complete API Guide

**Base URL**: `http://localhost:8000`
**API Version**: v1
**Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
**ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Authentication

All protected routes require a JWT Bearer token in the `Authorization` header.

### Obtain Token
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "adminpassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Use Token
```http
GET /api/v1/dashboard/1/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Onboarding

### Register a New Command Area
```http
POST /api/v1/onboarding/new-command-area
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Chambal Command Area",
  "bbox": [76.2, 25.8, 76.4, 26.0],
  "crops": ["wheat", "mustard", "rice"],
  "capacity_cusec": 1500.0,
  "season_label": "Kharif 2026"
}
```

**Response `201 Created`:**
```json
{
  "command_area_id": 2,
  "name": "Chambal Command Area",
  "fields_created": 7,
  "canals_created": 2,
  "status": "seeded",
  "message": "Command area registered and fields auto-seeded successfully."
}
```

---

## Explainability & Trust

### Get SHAP Pixel Attributions
```http
GET /api/v1/explain/{field_id}/why
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "predicted_crop": "wheat",
  "confidence": 0.91,
  "shap_top_features": [
    {"feature": "ndvi_day_15", "shap_value": 0.32, "direction": "positive"},
    {"feature": "ndvi_day_22", "shap_value": 0.28, "direction": "positive"},
    {"feature": "sar_vv_day_6", "shap_value": -0.14, "direction": "negative"},
    {"feature": "ndwi_day_10", "shap_value": 0.11, "direction": "positive"},
    {"feature": "evi_day_18", "shap_value": 0.09, "direction": "positive"}
  ],
  "explanation": "This field was classified as wheat primarily because of high NDVI values on days 15 and 22, consistent with peak winter wheat canopy development."
}
```

### Get Uncertainty Map
```http
GET /api/v1/uncertainty/{command_area_id}/map
```

**Response `200 OK`:**
```json
{
  "command_area_id": 1,
  "fields": [
    {
      "field_id": 1,
      "entropy": 0.12,
      "disagreement_index": 0.08,
      "confidence_category": "high"
    },
    {
      "field_id": 2,
      "entropy": 0.67,
      "disagreement_index": 0.41,
      "confidence_category": "low"
    }
  ],
  "flagged_for_review": [2]
}
```

---

## Drought & Climate

### Get SPEI Drought Indices
```http
GET /api/v1/drought/{command_area_id}/spei
```

**Response `200 OK`:**
```json
{
  "command_area_id": 1,
  "computed_at": "2026-06-21T00:00:00Z",
  "spei_1m": -0.82,
  "spei_3m": -1.43,
  "spei_6m": -1.91,
  "drought_category": "severe",
  "interpretation": "3-month SPEI of -1.43 indicates severe drought conditions over the last season."
}
```

---

## Phenology

### Get Current Growth Stage
```http
GET /api/v1/phenology/{field_id}/stage
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "crop_type": "wheat",
  "current_stage": "flowering",
  "stage_day": 75,
  "days_to_harvest": 38,
  "ndvi_current": 0.72,
  "gdd_accumulated": 1240.5,
  "advisory": "Critical stage — do not miss irrigation. Water stress during flowering reduces grain set by 20-40%."
}
```

---

## Stress Detection

### Detect Moisture Stress (Causal Gating)
```http
GET /api/v1/stress/{field_id}/detect
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "stress_detected": true,
  "stress_level": "moderate",
  "vci": 0.38,
  "smi": 0.29,
  "causal_gate": "stress_confirmed",
  "gate_reason": "VCI and SMI both below threshold. Phenological stage is vegetative — stress is not attributable to natural senescence.",
  "recommended_action": "Irrigate within 24-48 hours."
}
```

**When stress is a false positive (senescence):**
```json
{
  "stress_detected": false,
  "causal_gate": "senescence_suppressed",
  "gate_reason": "NDVI decline is consistent with natural crop senescence. No irrigation required."
}
```

---

## Water Balance

### Get Soil Water Balance
```http
GET /api/v1/water/{field_id}/balance
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "date": "2026-06-21",
  "et0_mm": 5.2,
  "etc_mm": 6.3,
  "eta_mm": 4.9,
  "depletion_mm": 42.1,
  "taw_mm": 120.0,
  "raw_mm": 60.0,
  "stress_coefficient_ks": 0.78,
  "et_source": "sebal"
}
```

---

## Irrigation Advisory

### Get Precision Irrigation Advisory
```http
GET /api/v1/irrigation/{field_id}/advisory
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "advisory_date": "2026-06-21",
  "irrigate": true,
  "water_depth_mm": 42.1,
  "volume_m3": 421.0,
  "timing": "irrigate_now",
  "deferred": false,
  "deferral_reason": null,
  "rainfall_forecast_mm": 2.0,
  "savings_vs_flood_m3": 168.0,
  "savings_inr": 336.0
}
```

**When deferred due to rainfall:**
```json
{
  "irrigate": false,
  "deferred": true,
  "deferral_reason": "Heavy rainfall of 35mm forecast in next 48 hours. Advisory deferred to avoid soil waterlogging.",
  "next_advisory_date": "2026-06-23"
}
```

---

## Economic & ROI

### Get Yield Forecast
```http
GET /api/v1/yield/{field_id}/forecast
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "crop_type": "wheat",
  "ndvi_integral": 18.42,
  "gdd_total": 1240.5,
  "yield_tonne_per_ha": 4.21,
  "ci_95_lower": 3.81,
  "ci_95_upper": 4.61,
  "national_average_tonne_per_ha": 3.5,
  "above_average_pct": 20.3
}
```

### Get Season Savings (ROI)
```http
GET /api/v1/roi/{field_id}/season-savings
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "season": "Rabi 2025-26",
  "field_area_ha": 1.0,
  "water_applied_m3": 4200.0,
  "flood_irrigation_benchmark_m3": 6300.0,
  "water_saved_m3": 2100.0,
  "water_saved_pct": 33.3,
  "electricity_saved_kwh": 105.0,
  "savings_inr": 6300.0,
  "co2_saved_kg": 84.0
}
```

### Get PMFBY Loss Evidence
```http
GET /api/v1/roi/{field_id}/pmfby-evidence
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "crop_type": "wheat",
  "season": "Rabi 2025-26",
  "stage_losses": {
    "emergence": 0.0,
    "vegetative": 5.2,
    "flowering": 18.4,
    "reproductive": 12.1,
    "senescence": 0.0
  },
  "weighted_loss_pct": 12.7,
  "verification_hash": "sha256:a3f9c2b1...",
  "timestamp": "2026-06-21T00:00:00Z",
  "audit_trail": "Hash covers: field_id=1, loss_pct=12.7, timestamp=2026-06-21T00:00:00Z"
}
```

---

## Spatial Intelligence

### Get Sub-Field Management Zones
```http
GET /api/v1/zonation/{field_id}/zones
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "num_zones": 3,
  "zones": [
    {
      "zone_id": "A",
      "pixel_count": 142,
      "area_ha": 0.42,
      "ndvi_mean": 0.74,
      "moisture_status": "adequate",
      "recommended_action": "Standard irrigation schedule"
    },
    {
      "zone_id": "B",
      "pixel_count": 87,
      "area_ha": 0.26,
      "ndvi_mean": 0.58,
      "moisture_status": "mild_stress",
      "recommended_action": "Increase irrigation frequency by 15%"
    },
    {
      "zone_id": "C",
      "pixel_count": 105,
      "area_ha": 0.32,
      "ndvi_mean": 0.31,
      "moisture_status": "severe_stress",
      "recommended_action": "Immediate irrigation required. Check for soil compaction."
    }
  ]
}
```

### Get Crop Rotation History
```http
GET /api/v1/rotation/{field_id}/history
```

**Response `200 OK`:**
```json
{
  "field_id": 1,
  "rotation_history": [
    {"season": "Rabi 2023-24", "crop": "wheat"},
    {"season": "Kharif 2024", "crop": "rice"},
    {"season": "Rabi 2024-25", "crop": "wheat"},
    {"season": "Kharif 2025", "crop": "fallow"},
    {"season": "Rabi 2025-26", "crop": "wheat"}
  ],
  "rotation_pattern": "wheat-rice-wheat-fallow-wheat",
  "consecutive_wheat_seasons": 2,
  "advisory": "Consider mustard in next Rabi season to break wheat-rice cycle and improve soil nitrogen."
}
```

---

## Farmer Advisory

### Get Voice Advisory (MP3)
```http
GET /api/v1/voice/{field_id}/audio?lang=hi
```

**Response**: Binary MP3 audio stream

```bash
# Download Hindi advisory
curl http://localhost:8000/api/v1/voice/1/audio?lang=hi --output advisory_hindi.mp3

# Download English advisory
curl http://localhost:8000/api/v1/voice/1/audio?lang=en --output advisory_english.mp3
```

**Hindi Advisory Script Example:**
> *"खेत संख्या एक में मध्यम जल तनाव पाया गया है। कृपया अगले 24 से 48 घंटों में 42 मिलीमीटर सिंचाई करें। यह गेहूं की फूल आने की अवस्था है — सिंचाई न करने पर उपज में 30% तक की कमी हो सकती है।"*

### Submit Farmer Feedback
```http
POST /api/v1/feedback/submit
Content-Type: application/json
```

**Request Body:**
```json
{
  "field_id": 1,
  "correct_crop": "mustard",
  "advisory_correct": false,
  "comment": "The system said wheat but we planted mustard this season."
}
```

**Response `201 Created`:**
```json
{
  "feedback_id": 42,
  "status": "queued",
  "priority_score": 0.87,
  "message": "Feedback recorded. Field flagged for active learning review."
}
```

### Get Active Learning Review Queue
```http
GET /api/v1/feedback/review-queue
```

**Response `200 OK`:**
```json
{
  "total_pending": 12,
  "fields": [
    {
      "field_id": 2,
      "disagreement_score": 0.91,
      "farmer_correction": "cotton",
      "model_prediction": "soybean",
      "priority": "high",
      "queued_at": "2026-06-21T00:00:00Z"
    }
  ]
}
```

---

## Data Quality

### Get Optical-SAR Triage Log
```http
GET /api/v1/data-quality/{command_area_id}/triage-log
```

**Response `200 OK`:**
```json
{
  "command_area_id": 1,
  "triage_log": [
    {
      "date": "2026-06-15",
      "sentinel2_cloud_cover": 0.78,
      "triage_decision": "sar_fallback",
      "sar_available": true,
      "note": "Cloud cover 78% — SAR backscatter promoted as primary input."
    },
    {
      "date": "2026-06-18",
      "sentinel2_cloud_cover": 0.12,
      "triage_decision": "optical_primary",
      "sar_available": true,
      "note": "Clear sky — Sentinel-2 optical used as primary."
    }
  ],
  "sar_fallback_pct": 62.5
}
```

---

## Dashboard

### Get Full Command Area Dashboard
```http
GET /api/v1/dashboard/{command_area_id}/summary
```

**Response `200 OK`:**
```json
{
  "command_area_id": 1,
  "name": "Sirhind-Bhakra Command Zone",
  "total_fields": 7,
  "total_area_ha": 7.0,
  "season": "Rabi 2025-26",
  "crop_distribution": {
    "wheat": 4,
    "mustard": 2,
    "fallow": 1
  },
  "stress_summary": {
    "no_stress": 3,
    "mild_stress": 2,
    "moderate_stress": 1,
    "severe_stress": 1
  },
  "drought_status": "moderate",
  "spei_3m": -1.43,
  "water_saved_m3_season": 14700.0,
  "savings_inr_season": 44100.0,
  "advisory_deferred_today": false
}
```

---

## HTTP Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| `400` | Bad Request | Invalid bbox format, missing required field |
| `401` | Unauthorized | Missing or expired JWT token |
| `403` | Forbidden | Token valid but insufficient permissions |
| `404` | Not Found | field_id or command_area_id does not exist |
| `422` | Unprocessable Entity | Pydantic validation error on request body |
| `500` | Internal Server Error | ML model error, DB connectivity issue |

---

## Rate Limiting

In production mode, API rate limits are enforced:

| Endpoint Group | Limit |
|---------------|-------|
| Auth endpoints | 10 req/min per IP |
| ML inference endpoints | 30 req/min per user |
| Voice advisory | 10 req/min per user |
| Dashboard & read | 120 req/min per user |

---

*Full interactive API documentation is always available at `http://localhost:8000/docs`*
