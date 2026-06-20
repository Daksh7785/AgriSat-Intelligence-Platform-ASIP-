import os
import datetime
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from shapely.geometry import Polygon, box
import geopandas as gpd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models

# Try to import GEE, log if not available
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False

class IngestionService:
    @staticmethod
    def initialize_gee():
        """Initializes Earth Engine client with service account if available."""
        if not GEE_AVAILABLE:
            return False
        try:
            if settings.GEE_SERVICE_ACCOUNT_KEY:
                # Assuming key is path to json key file
                credentials = ee.ServiceAccountCredentials(
                    "gee-service-account@agrisense.iam.gserviceaccount.com",
                    settings.GEE_SERVICE_ACCOUNT_KEY
                )
                ee.Initialize(credentials)
                return True
            else:
                ee.Initialize()
                return True
        except Exception as e:
            print(f"GEE initialization failed: {e}. Running in local/fallback mode.")
            return False

    @staticmethod
    def generate_synthetic_raster(
        output_dir: str,
        name: str,
        sensor: str,
        date: datetime.date,
        bbox: list = [75.0, 30.0, 75.2, 30.2]  # Left, bottom, right, top in Punjab, India
    ) -> str:
        """
        Generates a high-fidelity georeferenced GeoTIFF for testing.
        Optical sensors (Sentinel-2, Landsat-8) contain Red, Green, Blue, NIR, SWIR1, SWIR2 bands.
        SAR sensors (Sentinel-1) contain VV and VH bands.
        """
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{name}.tif")
        
        # Dimensions
        width, height = 200, 200
        
        # Geotransform
        transform = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], width, height)
        crs = "EPSG:4326"
        
        if sensor in ["Sentinel-2", "Landsat-8", "Landsat-9", "AWiFS", "LISS-III", "LISS-IV"]:
            # 6 bands: Blue, Green, Red, NIR, SWIR1, SWIR2
            count = 6
            dtype = 'float32'
            
            # Generate spatially coherent crop signatures
            # Create a grid of simulated fields
            x = np.linspace(0, 10, width)
            y = np.linspace(0, 10, height)
            xv, yv = np.meshgrid(x, y)
            
            # Base indices
            fields_mask = (np.sin(xv) * np.cos(yv) > 0).astype(np.float32)
            
            # High vegetative areas (crop) vs dry soil (fallow)
            # Add some temporal signature variation based on day of year
            day_of_year = date.timetuple().tm_yday
            season_factor = np.sin((day_of_year - 60) / 365.0 * 2 * np.pi)  # Peak in spring/autumn
            season_factor = max(0.1, (season_factor + 1.0) / 2.0)
            
            nir_base = 0.25 + 0.35 * fields_mask * season_factor
            red_base = 0.08 - 0.05 * fields_mask * season_factor
            green_base = 0.10 + 0.08 * fields_mask * season_factor
            blue_base = 0.06 - 0.02 * fields_mask * season_factor
            swir1_base = 0.20 - 0.08 * fields_mask * season_factor
            swir2_base = 0.15 - 0.07 * fields_mask * season_factor
            
            # Add noise
            noise = lambda: np.random.normal(0, 0.01, (height, width)).astype('float32')
            
            bands = [
                blue_base + noise(),
                green_base + noise(),
                red_base + noise(),
                nir_base + noise(),
                swir1_base + noise(),
                swir2_base + noise()
            ]
            
            # Clip bounds
            for idx in range(6):
                bands[idx] = np.clip(bands[idx], 0.0, 1.0)
                
        else: # SAR Sensor (Sentinel-1, EOS-04, NISAR)
            # 3 bands: VV, VH, VH/VV ratio (computed)
            count = 3
            dtype = 'float32'
            
            # SAR backscatter values in dB (typically VV -15 to -5 dB, VH -25 to -10 dB)
            x = np.linspace(0, 10, width)
            y = np.linspace(0, 10, height)
            xv, yv = np.meshgrid(x, y)
            fields_mask = (np.sin(xv) * np.cos(yv) > 0).astype(np.float32)
            
            # Crop growth attenuates SAR polarization ratio
            vv = -12.0 + 5.0 * fields_mask + np.random.normal(0, 0.5, (height, width))
            vh = -22.0 + 8.0 * fields_mask + np.random.normal(0, 0.5, (height, width))
            ratio = vh - vv # in dB this is VH/VV (subtraction in log space)
            
            bands = [
                vv.astype('float32'),
                vh.astype('float32'),
                ratio.astype('float32')
            ]
            
        # Write to GeoTIFF
        with rasterio.open(
            file_path, 'w',
            driver='GTiff',
            height=height,
            width=width,
            count=count,
            dtype=dtype,
            crs=crs,
            transform=transform
        ) as dst:
            for band_idx, band_data in enumerate(bands, 1):
                dst.write(band_data, band_idx)
                
        return file_path

    @staticmethod
    def trigger_temporal_ingestion(
        db: Session,
        sensor: str,
        start_date: datetime.date,
        end_date: datetime.date,
        bbox: list = [75.0, 30.0, 75.2, 30.2]
    ):
        """
        Triggers composite queries and downloads. 
        In DEMO_MODE, it generates multiple synthetic rasters to simulate historical observations.
        """
        output_dir = os.path.abspath(os.path.join("data", "rasters"))
        current_date = start_date
        step = datetime.timedelta(days=8)  # 8-day composite frequency
        
        raster_records = []
        
        while current_date <= end_date:
            name = f"{sensor.lower()}_{current_date.strftime('%Y%m%d')}"
            
            # Simulated download path
            file_path = IngestionService.generate_synthetic_raster(
                output_dir=output_dir,
                name=name,
                sensor=sensor,
                date=current_date,
                bbox=bbox
            )
            
            # Compute footprint polygon
            geom_poly = Polygon([
                (bbox[0], bbox[1]),
                (bbox[2], bbox[1]),
                (bbox[2], bbox[3]),
                (bbox[0], bbox[3]),
                (bbox[0], bbox[1])
            ])
            
            # Create DB entry
            from geoalchemy2.shape import from_shape
            db_raster = models.Raster(
                name=name,
                sensor=sensor,
                acquisition_date=current_date,
                file_path=file_path,
                cloud_cover=0.05 if sensor != "Sentinel-1" else 0.0,
                spatial_resolution=10.0 if sensor in ["Sentinel-2", "Sentinel-1"] else 30.0,
                geom=from_shape(geom_poly, srid=4326)
            )
            db.add(db_raster)
            raster_records.append(db_raster)
            
            current_date += step
            
        db.commit()
        for r in raster_records:
            db.refresh(r)
            
        return raster_records
