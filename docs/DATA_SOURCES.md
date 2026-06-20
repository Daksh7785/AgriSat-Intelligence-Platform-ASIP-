# 🛰️ Kisan Drishti — Data Sources Reference

This document details every external data source integrated into the Kisan Drishti platform, including access method, spatial/temporal resolution, licensing, and usage within the system.

---

## 1. Sentinel-2 MSI (Multispectral Instrument)

| Attribute | Detail |
|-----------|--------|
| **Provider** | European Space Agency (ESA) — Copernicus Programme |
| **Access** | Free, open access via Sentinel Hub, Google Earth Engine, AWS Open Data |
| **Spatial Resolution** | 10m (Bands 2,3,4,8) / 20m (Red-Edge, SWIR) / 60m (coastal, cirrus) |
| **Temporal Resolution** | 5-day revisit at equator (10-day per sensor) |
| **Processing Level** | L2A (Surface Reflectance, atmospherically corrected) |
| **License** | Copernicus Open Access — free for commercial and research use |

**Usage in Kisan Drishti:**
- NDVI, NDWI, EVI, SAVI computation for crop classification
- Phenological milestone detection via temporal NDVI profiles
- Cloud mask generation using Scene Classification Layer (SCL)
- Input to AutoML voting ensemble feature extraction (70-dim vector)

**Key Bands Used:**

| Band | Wavelength | Use |
|------|-----------|-----|
| B2 (Blue) | 490 nm | EVI blue correction |
| B3 (Green) | 560 nm | NDWI water index |
| B4 (Red) | 665 nm | NDVI, EVI |
| B8 (NIR) | 842 nm | NDVI, NDWI |
| B8A (Red-Edge) | 865 nm | Crop stress |
| B11 (SWIR1) | 1610 nm | Soil moisture proxy |
| B12 (SWIR2) | 2190 nm | Dry/wet soil discrimination |

---

## 2. Sentinel-1 GRD (Ground Range Detected SAR)

| Attribute | Detail |
|-----------|--------|
| **Provider** | ESA — Copernicus Programme |
| **Access** | Free, open access via ASF DAAC, Copernicus Data Space |
| **Spatial Resolution** | 10m (IW mode) |
| **Temporal Resolution** | 6-day revisit (combined A+B) |
| **Bands** | VV and VH dual-polarization (C-band, 5.4 GHz) |
| **License** | Copernicus Open Access |

**Usage in Kisan Drishti:**
- **All-weather soil moisture index (SMI)** — C-band backscatter penetrates clouds, enabling year-round monitoring
- **SAR-based irrigated area extent** — identifies irrigated fields from backscatter drops
- **Crop sowing date detection** — abrupt backscatter changes indicate soil tillage events
- **Cloud-cover fallback** — promoted to primary input when optical cloud cover > 60%
- **Refined Lee Speckle Filter** applied before feature extraction

---

## 3. NASA NISAR — L-Band SAR (Primary Future Data Source)

| Attribute | Detail |
|-----------|--------|
| **Provider** | NASA (USA) + ISRO (India) joint mission |
| **Launch** | 30 July 2025 |
| **Science Operations** | January 2026 (operational) |
| **Access** | NASA Alaska Satellite Facility (ASF) DAAC |
| **Spatial Resolution** | 3–10m (L-band, 1.25 GHz) |
| **Temporal Resolution** | 12-day repeat cycle |
| **Bands** | L-band HH, HV dual-polarization |
| **License** | NASA Open Data — free for all use |

**Usage in Kisan Drishti:**
- **Subsurface soil moisture** — L-band penetrates crop canopy and top 5–10 cm of soil, far superior to C-band for root zone moisture
- **Forest/crop biomass** — L-band backscatter correlates with above-ground biomass
- **Crop type discrimination** — HH/HV ratios distinguish between crop structures
- **Flood extent mapping** — supports disaster response for waterlogged field detection

**Connector Implementation:**
```python
# backend/app/data/nisar_connector.py
# Queries NASA CMR API:
# https://cmr.earthdata.nasa.gov/search/granules.json
# with temporal + spatial bbox filters
```

**CMR Query Example:**
```
https://cmr.earthdata.nasa.gov/search/granules.json
  ?short_name=NISAR_L1_PR_RSLC_001
  &bounding_box=76.2,25.8,76.4,26.0
  &temporal=2026-01-01T00:00:00Z,2026-06-01T00:00:00Z
  &page_size=20
```

---

## 4. MODIS MOD16A2 — Actual Evapotranspiration

| Attribute | Detail |
|-----------|--------|
| **Provider** | NASA LP DAAC |
| **Sensor** | Terra MODIS |
| **Spatial Resolution** | 500m |
| **Temporal Resolution** | 8-day cumulative composites |
| **Variable** | ET, PET (mm/8-day) |
| **License** | NASA Open Data |

**Usage in Kisan Drishti:**
- **ETa fallback** — used as actual evapotranspiration when Sentinel-2 thermal data or field weather stations are unavailable
- Converted to daily ETa by dividing by 8
- Compared against FAO-56 Penman-Monteith ET₀ to derive the water stress coefficient Ks

---

## 5. IMD Gridded Weather Data

| Attribute | Detail |
|-----------|--------|
| **Provider** | India Meteorological Department |
| **Spatial Resolution** | 0.25° × 0.25° (~25 km) |
| **Temporal Resolution** | Daily |
| **Variables** | Temperature (max/min), Humidity, Wind speed, Solar radiation, Precipitation |
| **Access** | IMD API (key required) / `imd_api_key` env variable |

**Usage in Kisan Drishti:**
- **FAO-56 Penman-Monteith ET₀** — daily reference evapotranspiration calculation
- **3-day rainfall forecast integration** — defers irrigation advisories before predicted heavy rainfall
- **SPEI** — monthly Precipitation - ET₀ for drought severity computation
- **GDD (Growing Degree Days)** — cumulative heat units for yield forecasting

**Variables Required for ET₀:**

| Variable | Symbol | Unit |
|----------|--------|------|
| Max temperature | T_max | °C |
| Min temperature | T_min | °C |
| Relative humidity | RH | % |
| Wind speed at 2m | u₂ | m/s |
| Solar radiation | Rs | MJ/m²/day |

---

## 6. Google Earth Engine (GEE) — Optional Integration

| Attribute | Detail |
|-----------|--------|
| **Provider** | Google |
| **Access** | GEE account + service account key required |
| **Usage** | Cloud-based preprocessing of Sentinel-1/2 time series |
| **Config** | `USE_SAMPLE_DATA=false` + `GEE_KEY_FILE` |

**Usage in Kisan Drishti (when enabled):**
- Large-scale temporal compositing of Sentinel-2 for cloud-free mosaics
- Automated computation of NDVI/EVI stacks over command area polygons
- Export of preprocessed feature arrays to MinIO for downstream ML

> 🟡 **GEE is optional.** The system runs fully with synthetic data (`USE_SAMPLE_DATA=true`) for development and demo purposes.

---

## Data Pipeline Summary

```
Raw Satellite Data
      │
      ├── Sentinel-2 L2A ──────┐
      ├── Sentinel-1 GRD ──────┼──► Cloud Triage ──► Speckle Filter ──► Feature Extraction
      ├── NISAR L-band ────────┘                                               │
      │                                                                         ▼
      └── IMD Weather ──────────────────────────────────────────────► FAO-56 ET₀ Engine
                                                                               │
                                                                               ▼
                                                                        AI/ML Pipeline
```

---

## Offline / Demo Mode

When `USE_SAMPLE_DATA=true` (default), the platform generates synthetic but realistic:
- Per-field 30-day NDVI/NDWI timeseries (seasonal sigmoid curves + noise)
- SAR VV/VH backscatter arrays (crop-type specific distributions)
- IMD weather timeseries (typical Punjab Rabi season climate)
- Ground truth crop labels for classifier training/validation

This allows full platform demonstration without any external API keys.
