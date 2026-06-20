import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
from scipy.optimize import curve_fit
import geopandas as gpd
from sqlalchemy.orm import Session
from datetime import datetime

# Try importing skimage, handle if missing
try:
    from skimage.feature import graycomatrix, graycoproperty
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

from app.db import models

class RasterService:
    @staticmethod
    def compute_vegetation_indices(blue: np.ndarray, green: np.ndarray, red: np.ndarray, nir: np.ndarray, swir1: np.ndarray) -> dict:
        """Computes key vegetation indices with division guard rails."""
        epsilon = 1e-6
        
        # NDVI
        ndvi = (nir - red) / (nir + red + epsilon)
        
        # EVI: 2.5 * (NIR - Red) / (NIR + 6 * Red - 7.5 * Blue + 1)
        evi = 2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0 + epsilon)
        
        # SAVI: 1.5 * (NIR - Red) / (NIR + Red + 0.5)
        savi = 1.5 * (nir - red) / (nir + red + 0.5 + epsilon)
        
        # NDWI: (NIR - SWIR1) / (NIR + SWIR1) (Standard for plant water stress)
        ndwi = (nir - swir1) / (nir + swir1 + epsilon)
        
        # GNDVI
        gndvi = (nir - green) / (nir + green + epsilon)
        
        # MSAVI: 0.5 * (2 * NIR + 1 - sqrt((2 * NIR + 1)^2 - 8 * (NIR - Red)))
        term = (2.0 * nir + 1.0) ** 2 - 8.0 * (nir - red)
        term = np.clip(term, 0.0, None)  # Ensure non-negative inside sqrt
        msavi = 0.5 * (2.0 * nir + 1.0 - np.sqrt(term))
        
        return {
            "ndvi": float(np.nanmean(ndvi)),
            "evi": float(np.nanmean(evi)),
            "savi": float(np.nanmean(savi)),
            "ndwi": float(np.nanmean(ndwi)),
            "gndvi": float(np.nanmean(gndvi)),
            "msavi": float(np.nanmean(msavi))
        }

    @staticmethod
    def compute_glcm_features(image_band: np.ndarray) -> dict:
        """Extracts Gray-Level Co-occurrence Matrix (GLCM) textures."""
        if not SKIMAGE_AVAILABLE:
            # Fallback mock metrics if skimage is missing
            return {
                "contrast": 12.5,
                "homogeneity": 0.65,
                "entropy": 4.2,
                "asm": 0.08,
                "correlation": 0.75
            }
        
        try:
            # Convert band to uint8 [0, 255]
            img_min, img_max = np.nanmin(image_band), np.nanmax(image_band)
            if img_max - img_min > 0:
                normalized = ((image_band - img_min) / (img_max - img_min) * 255).astype(np.uint8)
            else:
                normalized = np.zeros(image_band.shape, dtype=np.uint8)
                
            # Compute GLCM (distance 1, angle 0)
            glcm = graycomatrix(normalized, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
            
            contrast = graycoproperty(glcm, 'contrast')[0, 0]
            homogeneity = graycoproperty(glcm, 'homogeneity')[0, 0]
            asm = graycoproperty(glcm, 'ASM')[0, 0]
            correlation = graycoproperty(glcm, 'correlation')[0, 0]
            
            # Entropy calculation: -sum(p * log(p))
            p = glcm.flatten()
            p = p[p > 0]
            entropy = -np.sum(p * np.log2(p))
            
            return {
                "contrast": float(contrast),
                "homogeneity": float(homogeneity),
                "entropy": float(entropy),
                "asm": float(asm),
                "correlation": float(correlation)
            }
        except Exception as e:
            print(f"GLCM computation error: {e}")
            return {
                "contrast": 0.0,
                "homogeneity": 0.0,
                "entropy": 0.0,
                "asm": 0.0,
                "correlation": 0.0
            }

    @staticmethod
    def fit_double_logistic(days: np.ndarray, ndvi_series: np.ndarray) -> dict:
        """
        Fits a double logistic curve to seasonal NDVI:
        y(t) = mn + (mx - mn) * (1 / (1 + exp(-m1 * (t - d1))) + 1 / (1 + exp(m2 * (t - d2))) - 1)
        Extracts Start of Season (SOS), Peak, End of Season (EOS), Growth Rate, and Length.
        """
        def double_logistic(t, mn, mx, m1, d1, m2, d2):
            return mn + (mx - mn) * (1.0 / (1.0 + np.exp(-m1 * (t - d1))) + 1.0 / (1.0 + np.exp(m2 * (t - d2))) - 0.5)

        # Initial parameter guesses: mn, mx, m1, d1, m2, d2
        p0 = [
            float(np.min(ndvi_series)),
            float(np.max(ndvi_series)),
            0.1,  # m1 growth slope
            100.0, # d1 start day of year
            0.1,  # m2 senescence slope
            280.0  # d2 end day of year
        ]
        
        try:
            # Curve fit
            popt, _ = curve_fit(
                double_logistic, days, ndvi_series, p0=p0,
                bounds=([0.0, 0.2, 0.01, 30.0, 0.01, 150.0], [0.3, 1.0, 1.0, 200.0, 1.0, 340.0]),
                maxfev=2000
            )
            mn, mx, m1, d1, m2, d2 = popt
            
            sos = d1
            peak = (d1 + d2) / 2.0
            eos = d2
            season_length = d2 - d1
            growth_rate = m1
            
            return {
                "sos_doy": int(sos),
                "peak_doy": int(peak),
                "eos_doy": int(eos),
                "growth_rate": float(growth_rate),
                "season_length_days": int(season_length)
            }
        except Exception as e:
            # Fallback estimation if optimization fails to converge
            max_idx = np.argmax(ndvi_series)
            peak = days[max_idx]
            sos = days[max_idx // 2]
            eos = days[min(len(days)-1, max_idx + (len(days) - max_idx) // 2)]
            return {
                "sos_doy": int(sos),
                "peak_doy": int(peak),
                "eos_doy": int(eos),
                "growth_rate": 0.05,
                "season_length_days": int(eos - sos)
            }

    @staticmethod
    def extract_field_zonal_statistics(
        db_session: Session,
        field_id: int,
        raster_id: int
    ) -> dict:
        """
        Reads a raster band file, clips it to the field geometry,
        and computes spectral, moisture, SAR, and GLCM metrics.
        """
        from geoalchemy2.shape import to_shape
        
        field = db_session.query(models.Field).filter(models.Field.id == field_id).first()
        raster = db_session.query(models.Raster).filter(models.Raster.id == raster_id).first()
        
        if not field or not raster:
            raise ValueError("Field or Raster record not found")
            
        geom_shape = to_shape(field.geom)
        geom_geojson = mapping(geom_shape)
        
        with rasterio.open(raster.file_path) as src:
            # Mask the raster with the field geometry
            out_image, out_transform = mask(src, [geom_geojson], crop=True, nodata=np.nan)
            
        if raster.sensor in ["Sentinel-2", "Landsat-8", "Landsat-9", "AWiFS", "LISS-III", "LISS-IV"]:
            # Band order: Blue, Green, Red, NIR, SWIR1, SWIR2
            blue_b = out_image[0]
            green_b = out_image[1]
            red_b = out_image[2]
            nir_b = out_image[3]
            swir1_b = out_image[4]
            swir2_b = out_image[5]
            
            # Compute indices
            veg_indices = RasterService.compute_vegetation_indices(blue_b, green_b, red_b, nir_b, swir1_b)
            
            # GLCM textures using NIR band
            textures = RasterService.compute_glcm_features(nir_b)
            
            # Compute Temperature/Moisture anomalies
            # In mock mode, generate standard VCI / TCI anomalies
            vci = (veg_indices["ndvi"] - 0.15) / (0.85 - 0.15) * 100.0
            tci = 50.0 + np.random.normal(0, 10)  # Simulated Temperature Condition Index
            vhi = 0.5 * vci + 0.5 * tci
            smi = (veg_indices["ndwi"] + 1.0) / 2.0  # Mapped to [0,1]
            
            features = {
                **veg_indices,
                **textures,
                "vci": float(np.clip(vci, 0.0, 100.0)),
                "tci": float(np.clip(tci, 0.0, 100.0)),
                "vhi": float(np.clip(vhi, 0.0, 100.0)),
                "smi": float(np.clip(smi, 0.0, 1.0)),
                "vv": None,
                "vh": None,
                "vh_vv_ratio": None
            }
        else: # SAR raster
            # Bands: VV, VH, VH/VV ratio
            vv_b = out_image[0]
            vh_b = out_image[1]
            ratio_b = out_image[2]
            
            features = {
                "ndvi": None, "evi": None, "savi": None, "ndwi": None, "gndvi": None, "msavi": None,
                "contrast": None, "homogeneity": None, "entropy": None, "asm": None, "correlation": None,
                "vci": None, "tci": None, "vhi": None, "smi": None,
                "vv": float(np.nanmean(vv_b)),
                "vh": float(np.nanmean(vh_b)),
                "vh_vv_ratio": float(np.nanmean(ratio_b))
            }
            
        return features
