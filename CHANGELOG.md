# 📋 CHANGELOG

All notable changes to **Kisan Drishti** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-06-21

### Added
- 🌟 **20 Innovation Features** fully implemented across 7 themes (Trust, Climate, Economic, Spatial, Farmer, Robustness, Scale)
- 📡 **NASA NISAR CMR Connector** — live L-band HH/HV granule search via `cmr.earthdata.nasa.gov`
- 🗣️ **Bilingual TTS Voice Advisories** — Hindi + English MP3 synthesis via `gTTS`
- 🔐 **PMFBY Loss Evidence Generator** — SHA-256 tamper-proof yield-loss hashes for crop insurance
- 📊 **Pixel-Level SHAP Attributions** — per-field XGBoost decision explanations
- 🌡️ **Log-Logistic SPEI Engine** — 3-parameter L-moment fitted drought severity index
- 🗺️ **Sub-Field K-Means Zonation** — 2–4 management zones from NDVI/SAR pixel clustering
- 🔁 **Crop Rotation Streak Tracker** — historical rotation sequence analysis per field
- 🌧️ **Rain-Aware Advisory Deferral** — IMD 3-day forecast integration
- 🤖 **Active Learning Feedback Loop** — farmer corrections trigger prioritized retraining queue
- 🛰️ **Optical-SAR Fallback Triage** — automatic SAR promotion when cloud cover > 60%
- 🔭 **Ground Truth Provenance Badges** — synthetic vs real data labelling on dashboard
- 📡 **Onboarding REST API** — auto-seeds command area, canals, and fields from bbox

### Improved
- Upgraded `README.md` to 700+ lines — full architecture, math formulations, DB schema, K8s, Terraform, security, monitoring, contributing, and impact sections
- Upgraded `docs/DATA_SOURCES.md` and `docs/MODEL_CARDS.md` with deeper coverage
- Added `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, and `CODE_OF_CONDUCT.md`

### Fixed
- Pydantic V2 migration warnings resolved across all schema files
- `datetime.utcnow()` deprecation replaced with `datetime.now(timezone.utc)`

---

## [1.1.0] — 2026-06-20

### Added
- 🏗️ **Full Backend Microservice Architecture** — FastAPI + Celery + PostGIS + Redis
- 🌐 **Next.js 15 + React 19 Frontend** — Leaflet GIS map, AI Copilot panel, data-quality components
- 🧠 **AutoML Voting Ensemble** — XGBoost + Random Forest soft-vote crop classifier
- 📈 **Bi-LSTM Phenology Tracker** — seasonal NDVI trajectory → growth milestone
- 🌾 **Ridge Regression Yield Forecaster** — NDVI integral + GDD crop-specific models
- 💧 **FAO-56 Penman-Monteith ET₀** — daily reference evapotranspiration engine
- 🔥 **SEBAL Actual ETa Engine** — surface energy balance with MOD16 fallback
- 🗄️ **PostGIS Schema** — spatial tables for command areas, canals, fields, timeseries
- ⚙️ **Celery Beat Scheduler** — 6-hourly satellite ingestion + weekly model retraining cron
- 🐋 **Docker Compose Stack** — one-command full local deployment
- ☸️ **Kubernetes Manifests** — StatefulSet for DB, HPA for backend, NGINX ingress
- 🏗️ **Terraform IaC** — AWS VPC + RDS + ElastiCache + EKS provisioning
- 🔬 **40-test Pytest Suite** — 100% pass rate covering all innovation modules

### Added Data Connectors
- `nisar_connector.py` — NASA ASF DAAC CMR search
- `cloud_triage_logger.py` — cloud QA + SAR fallback logic
- `sample_data_generator.py` — synthetic bbox grid-farm seeder

### Added Services
- `voice_advisory_service.py` — bilingual TTS synthesizer
- `feedback_loop_service.py` — active learning queue manager
- `onboarding_service.py` — auto command-area registration + field seeding
- `irrigation_scheduler.py` — rain-aware deferral logic

---

## [1.0.0] — 2026-06-19

### Added
- ✅ Initial repository structure
- ✅ FastAPI app bootstrap (`main.py`, `dependencies.py`)
- ✅ Pydantic settings configuration (`core/config.py`)
- ✅ PostGIS async session factory (`core/database.py`)
- ✅ Redis cache client (`core/cache.py`)
- ✅ SQLAlchemy ORM models with PostGIS geometry (`db/models.py`)
- ✅ Initial Celery app + beat schedule (`tasks/celery_app.py`)
- ✅ `.env.example` with full environment variable template
- ✅ `.gitignore` with Python, Node.js, Docker and secret exclusions
- ✅ GitHub Actions CI pipeline (`ci.yml`)
- ✅ `GIS_pipeline/seed_db.py` — auto-seeder for pilot command area data

---

## Unreleased / Roadmap

### Planned for v1.3.0
- [ ] RESOURCESAT-2A (IRS) data connector for India-specific band analysis
- [ ] Tamil, Telugu, Kannada language TTS advisories
- [ ] React Native mobile app (Android-first)
- [ ] WhatsApp Bot integration (Twilio) for voice advisory delivery
- [ ] Grafana dashboard templates for production monitoring
- [ ] Online model fine-tuning with farmer-provided ground truth photos
- [ ] Shapefile/KML export for offline GIS use

### Planned for v2.0.0
- [ ] Full multi-tenant SaaS architecture (per-state isolation)
- [ ] API rate limiting and usage quotas
- [ ] Federated learning across state agricultural departments
- [ ] Real-time stream processing (Apache Kafka + Flink)
- [ ] PMFBY direct API integration with crop insurance portal

---

*Maintained by the Kisan Drishti development team.*
