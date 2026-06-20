# Kisan Drishti Data Sources

## NISAR Status (Corrected & Operational)
NISAR (NASA-ISRO Synthetic Aperture Radar) launched on 30 July 2025 and entered its science operations phase in January 2026. NISAR L-band data products are now fully operational and released through NASA's Alaska Satellite Facility (ASF) DAAC. 

Our architecture supports NISAR L-band HH/HV dual-polarization SAR backscatter:
- **Connector**: Implemented in `backend/app/data/nisar_connector.py`
- **Metadata Querying**: Automatically builds spatial and temporal queries against the NASA Common Metadata Repository (CMR) search API at `https://cmr.earthdata.nasa.gov/search/granules.json`.
- **Integrations**: Supports downloading and mapping L-band H5/GeoTIFF backscatter arrays into the crop classification and moisture stress detection pipelines.

## Other Data Sources
- **Sentinel-2 L2A**: 10m spatial resolution optical bands (NIR, Red, Blue, Green, SWIR) used for crop classification, phenology tracking, and vegetation indices (NDVI, EVI, SAVI).
- **Sentinel-1 GRD**: C-band SAR dual-polarization (VV, VH) backscatter time series, used for all-weather soil moisture index (SMI) calculation and crop sowing date detection.
- **MODIS MOD16A2**: actual evapotranspiration (ETa) 8-day cumulative dataset used as a fallback for crop water deficit computations.
- **IMD Weather Data**: daily gridded weather datasets for reference evapotranspiration (ET0) estimation via Penman-Monteith.
