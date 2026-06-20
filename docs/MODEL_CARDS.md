# 🧠 Kisan Drishti — Model Cards

This document provides AI model cards for every machine learning model deployed in the Kisan Drishti platform. Each card follows the [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) framework (Mitchell et al., 2018).

---

## Model Card 1: AutoML Voting Ensemble — Crop Classifier

### Model Details
| Attribute | Detail |
|-----------|--------|
| **Model Type** | Soft-Voting Ensemble (XGBoost + Random Forest) |
| **Version** | 1.2.0 |
| **Framework** | scikit-learn 1.4.x + xgboost 2.x |
| **Training Data** | India Crop Type Map (ICTM) + synthetic GEE-derived field labels |
| **License** | MIT (same as platform) |

### Inputs

| Feature | Shape | Description |
|---------|-------|-------------|
| NDVI time-series | (30,) | Daily NDVI over last 30 days |
| NDWI time-series | (30,) | Daily NDWI over last 30 days |
| EVI time-series | (30,) | Daily EVI over last 30 days |
| SAR VV/VH ratios | (10,) | 10-day Sentinel-1 VV/VH backscatter ratios |
| **Total** | **(70,)** | **Concatenated feature vector** |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `crop_type` | str | Predicted crop label |
| `probability` | float | Ensemble confidence (0.0–1.0) |
| `uncertainty` | float | Shannon entropy of probability vector |

### Target Classes
`Wheat`, `Rice/Paddy`, `Cotton`, `Sugarcane`, `Maize`, `Soybean`, `Groundnut`, `Mustard/Rapeseed`, `Vegetables`, `Fallow/Barren`

### Performance Metrics (Synthetic Validation Set)
| Metric | Value |
|--------|-------|
| Overall Accuracy | ~87% |
| Macro F1-Score | ~0.84 |
| Cohen's Kappa | ~0.81 |
| Inference Time | < 5ms/field |

### Known Limitations
- Accuracy drops for small fields (< 0.5 ha) where pixels mix across crop boundaries
- Performance degrades for unusual phenological timings (e.g., unseasonal planting)
- Not validated on North-East India hill farming systems

### Ethical Considerations
- Model predictions are always accompanied by SHAP attributions to ensure transparency
- Uncertainty scores are surfaced in the dashboard so users are not misled by low-confidence predictions
- Active Learning feedback loop allows farmers to correct wrong predictions

---

## Model Card 2: Bi-LSTM Phenology Tracker

### Model Details
| Attribute | Detail |
|-----------|--------|
| **Model Type** | Bidirectional Long Short-Term Memory (Bi-LSTM) |
| **Framework** | PyTorch 2.x |
| **Architecture** | 2× Bi-LSTM layers (hidden=128) → Dropout(0.3) → Dense(6) → Softmax |
| **Parameters** | ~820,000 |
| **Training Data** | Synthetic seasonal NDVI curves labelled by crop calendar (FAO + IIPR) |

### Inputs
| Feature | Shape | Description |
|---------|-------|-------------|
| NDVI | (T, 1) | Variable-length seasonal NDVI trajectory |
| EVI | (T, 1) | Variable-length seasonal EVI trajectory |
| VH/VV ratio | (T//6, 1) | SAR backscatter time-series (every 6 days) |
| GDD | (T, 1) | Cumulative Growing Degree Days |

### Outputs
| Class | Label | Description |
|-------|-------|-------------|
| 0 | `emergence` | Seedling (NDVI < 0.2) |
| 1 | `vegetative` | Canopy development (0.2–0.6) |
| 2 | `flowering` | Reproductive initiation (peak NDVI) |
| 3 | `reproductive` | Grain/fruit fill |
| 4 | `senescence` | Leaf senescence (declining NDVI) |
| 5 | `harvest` | Post-harvest (NDVI < 0.15) |

### Performance Metrics
| Metric | Value |
|--------|-------|
| Stage Classification Accuracy | ~83% |
| ±1 Stage Tolerance Accuracy | ~96% |
| Inference Time | < 10ms/sequence |

### Known Limitations
- Requires a minimum of 15 cloud-free observations; performance degrades below 10
- Does not model ratoon crops or multi-harvest systems
- Irrigation-induced greenness spikes may be misclassified as re-emergence

---

## Model Card 3: Ridge Regression Yield Forecaster

### Model Details
| Attribute | Detail |
|-----------|--------|
| **Model Type** | Crop-specific Ridge Regression (L2 regularized) |
| **Framework** | scikit-learn |
| **Regularization** | α = 0.5 |
| **Separate Models** | One per major crop class (10 models) |

### Inputs
| Feature | Description |
|---------|-------------|
| `ndvi_integral` | Cumulative NDVI area under the curve from emergence to flowering |
| `gdd_total` | Total Growing Degree Days (GDD) for the season |
| `rain_mm` | Seasonal total effective rainfall (mm) |
| `et_deficit_mm` | Total ET deficit over growing season (mm) |

### Outputs
| Output | Unit | Description |
|--------|------|-------------|
| `yield_tonne_per_ha` | t/ha | Predicted crop yield |
| `95_ci_lower` | t/ha | 95% confidence interval lower bound |
| `95_ci_upper` | t/ha | 95% confidence interval upper bound |

### Reference Yield Benchmarks (India)
| Crop | National Average | Model Target |
|------|----------------|-------------|
| Wheat | 3.5 t/ha | ±0.4 t/ha RMSE |
| Rice | 2.6 t/ha | ±0.3 t/ha RMSE |
| Maize | 3.1 t/ha | ±0.5 t/ha RMSE |
| Cotton | 0.51 t/ha (lint) | ±0.06 t/ha RMSE |

### Known Limitations
- Predictions are only valid from vegetative stage onwards (NDVI integral requires 30+ days)
- Does not account for pest/disease damage not visible in NDVI
- Assumes normal soil fertility levels; highly degraded soils may overestimate yields

---

## Model Card 4: K-Means Sub-Field Zonation

### Model Details
| Attribute | Detail |
|-----------|--------|
| **Algorithm** | K-Means (Lloyd's algorithm) |
| **k Selection** | Elbow method on within-cluster sum of squares (k = 2 to 4) |
| **Framework** | scikit-learn |
| **Convergence** | max_iter=300, n_init=10 |

### Inputs
| Feature | Description |
|---------|-------------|
| `ndvi_mean` | 30-day mean NDVI per pixel |
| `ndwi_mean` | 30-day mean NDWI per pixel |
| `sar_vv_db` | Sentinel-1 VV backscatter (dB) |

### Outputs
| Output | Description |
|--------|-------------|
| Zone A | High fertility, adequate moisture |
| Zone B | Moderate stress, variable moisture |
| Zone C | Low fertility or compaction |
| Zone D | Severe deficit (if k=4) |

### Known Limitations
- Assumes pixel-level feature homogeneity; does not model spatial autocorrelation
- Very small fields (< 1 ha) often result in 2-zone solutions only
- SAR speckle, even after Lee filtering, can create spurious zone boundaries

---

## Model Card 5: SEBAL Actual ET Engine

### Model Details
| Attribute | Detail |
|-----------|--------|
| **Method** | Surface Energy Balance Algorithm for Land (SEBAL) |
| **Reference** | Bastiaanssen et al. (1998), Remote Sensing of Environment |
| **Fallback** | NASA MODIS MOD16A2 (8-day ET product) |

### Inputs
| Variable | Source |
|----------|--------|
| Thermal IR brightness temperature | Landsat-8/9 Band 10 or MODIS |
| Surface albedo | Sentinel-2 derived |
| NDVI | Sentinel-2 |
| Wind speed | IMD gridded weather |
| Air temperature | IMD gridded weather |

### Outputs
| Output | Unit | Description |
|--------|------|-------------|
| `eta_mm_day` | mm/day | Actual evapotranspiration |
| `source` | str | `"sebal"` or `"mod16"` |

---

## Model Card 6: Log-Logistic SPEI Engine

### Model Details
| Attribute | Detail |
|-----------|--------|
| **Index** | Standardized Precipitation Evapotranspiration Index (SPEI) |
| **Reference** | Vicente-Serrano et al. (2010), Journal of Climate |
| **Distribution** | 3-parameter Log-Logistic fitted via L-moments |
| **Timescales** | 1-month, 3-month, 6-month |

### SPEI Interpretation
| SPEI Value | Category |
|-----------|---------|
| > +2.0 | Extremely wet |
| +1.0 to +2.0 | Moderately wet |
| -1.0 to +1.0 | Near normal |
| -1.0 to -1.5 | Moderate drought |
| -1.5 to -2.0 | Severe drought |
| < -2.0 | Extreme drought |

### Outputs
| Output | Description |
|--------|-------------|
| `spei_1m` | 1-month SPEI (immediate drought signal) |
| `spei_3m` | 3-month SPEI (seasonal drought signal) |
| `spei_6m` | 6-month SPEI (hydrological drought signal) |

### Known Limitations
- Requires minimum 30-year baseline climatology for reliable parameter fitting
- Sensitive to ET₀ estimation quality — IMD gridded data gaps affect accuracy
- Not suitable for hourly or sub-daily drought monitoring

---

## Overall Model Governance

### Retraining Policy
- **Trigger**: Active Learning Queue exceeds 50 farmer-flagged corrections
- **Schedule**: Celery Beat weekly cron (every Sunday 02:00 IST)
- **Validation**: Models are only promoted to production if new accuracy ≥ previous − 1%
- **Logging**: All training runs logged to MLflow at `http://localhost:5000`

### Bias & Fairness
- All models are validated separately on small (<1 ha), medium (1–5 ha), and large (>5 ha) holdings
- Farmer feedback loop is designed to surface systematic prediction errors for specific regions or crops

### Explainability
- Every AutoML prediction is accompanied by SHAP attributions (Top-5 features)
- Uncertainty scores are always shown to users alongside predictions
- Dashboard Provenance Badge indicates whether predictions are based on real or synthetic satellite data
