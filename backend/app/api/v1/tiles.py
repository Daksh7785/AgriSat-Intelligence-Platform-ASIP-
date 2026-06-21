from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFilter
import io
import math
import random

router = APIRouter(prefix="/tiles", tags=["Dynamic Satellite Tiles"])

@router.get("/{layer_type}/{z}/{x}/{y}")
def get_satellite_tile(layer_type: str, z: int, x: int, y: int):
    """
    Serves dynamic, semi-transparent satellite imagery grids (256x256 PNGs)
    seeded deterministically by tile coordinates so panning/zooming remains consistent.
    """
    tile_size = 256
    # Seed based on tile coordinates to make the visual features persistent
    seed_val = abs((x * 12345 + y * 6789) ^ (z * 999))
    random.seed(seed_val)

    # Create transparent image
    img = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw simulated satellite overlay based on layer type
    if layer_type == "ndvi":
        # Green to Red gradient spots representing vegetation index
        for _ in range(12):
            cx = random.randint(0, tile_size)
            cy = random.randint(0, tile_size)
            radius = random.randint(20, 60)
            ndvi_val = random.random() # 0 to 1
            
            # High NDVI -> Rich Green. Low NDVI -> Bare soil Red/Yellow
            if ndvi_val > 0.65:
                color = (16, 185, 129, int(80 + ndvi_val * 70)) # Emerald green
            elif ndvi_val > 0.4:
                color = (251, 191, 36, int(60 + ndvi_val * 60)) # Amber/yellow
            else:
                color = (239, 68, 68, int(40 + ndvi_val * 50)) # Red
                
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

    elif layer_type == "ndwi":
        # Blue gradient representing soil moisture and surface water index
        for _ in range(8):
            cx = random.randint(0, tile_size)
            cy = random.randint(0, tile_size)
            radius = random.randint(30, 80)
            ndwi_val = random.random()
            
            # Deep blue to cyan moisture colors
            color = (59, 130, 246, int(60 + ndwi_val * 120))
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

    elif layer_type == "sar":
        # SAR Radar Polarizations (VH/VV backscatter) - orange/yellow radar textures
        for _ in range(15):
            cx = random.randint(0, tile_size)
            cy = random.randint(0, tile_size)
            radius = random.randint(15, 45)
            sar_val = random.random()
            
            # Polarized backscatter simulation
            color = (99, 102, 241, int(40 + sar_val * 90)) # Indigo backscatter
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

    # Apply light blur to simulate smooth interpolation of satellite grids
    img = img.filter(ImageFilter.GaussianBlur(radius=8))

    # Save to memory buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return StreamingResponse(buf, media_type="image/png")
