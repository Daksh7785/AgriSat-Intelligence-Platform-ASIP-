import datetime
import urllib.parse
import httpx
from typing import List, Dict, Any, Optional
from loguru import logger

class NISARConnector:
    """
    NASA-ISRO Synthetic Aperture Radar (NISAR) L-band ASF DAAC CMR Connector.
    Enables metadata querying and retrieval of L-band backscatter products (HH, HV, VV, VH).
    """
    CMR_GRANULE_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
    
    def __init__(self, provider: str = "ASF"):
        self.provider = provider
        
    def build_cmr_query(
        self,
        bbox: List[float],
        start_date: datetime.date,
        end_date: datetime.date,
        short_name: str = "NISAR_L1_S_SLC"
    ) -> str:
        """
        Builds the NASA CMR search query URL.
        bbox format: [min_lon, min_lat, max_lon, max_lat]
        """
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        temporal_str = f"{start_date.isoformat()}T00:00:00Z,{end_date.isoformat()}T23:59:59Z"
        
        params = {
            "provider": self.provider,
            "short_name": short_name,
            "bounding_box": bbox_str,
            "temporal": temporal_str,
            "page_size": 50
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.CMR_GRANULE_URL}?{query_string}"

    async def query_asf_daac_metadata(
        self,
        bbox: List[float],
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[Dict[str, Any]]:
        """
        Queries NASA's CMR API for NISAR L-band products.
        Returns a structured list of granule assets with their HH/HV polarizations.
        Fails gracefully and returns simulated metadata in case of offline/test environments.
        """
        query_url = self.build_cmr_query(bbox, start_date, end_date)
        logger.info(f"Querying NASA CMR Search API: {query_url}")
        
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(query_url)
                if response.status_code == 200:
                    data = response.json()
                    feed = data.get("feed", {})
                    entries = feed.get("entry", [])
                    if entries:
                        return self._parse_cmr_response(entries)
                    else:
                        logger.info("NASA CMR returned 0 granules. Falling back to simulated catalog.")
        except Exception as e:
            logger.warning(f"CMR query failed or timed out: {e}. Falling back to NISAR simulated catalog.")
            
        return self._generate_simulated_nisar_metadata(bbox, start_date, end_date)


    def _parse_cmr_response(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for entry in entries:
            granule_id = entry.get("title", "")
            time_start = entry.get("time_start", "")
            
            boxes = entry.get("boxes", [])
            polygon = []
            if boxes:
                coords = [float(x) for x in boxes[0].split()]
                polygon = [(coords[1], coords[0]), (coords[3], coords[2])]
                
            links = entry.get("links", [])
            download_url = ""
            for link in links:
                href = link.get("href", "")
                if href.endswith(".h5") or href.endswith(".tif"):
                    download_url = href
                    break
                    
            results.append({
                "granule_id": granule_id,
                "acquisition_time": time_start,
                "sensor": "NISAR",
                "frequency_band": "L-band",
                "polarizations": ["HH", "HV"],
                "spatial_bounds": polygon,
                "download_url": download_url or f"https://datapool.asf.alaska.edu/NISAR/{granule_id}.zip",
                "status": "archived"
            })
        return results

    def _generate_simulated_nisar_metadata(
        self,
        bbox: List[float],
        start_date: datetime.date,
        end_date: datetime.date
    ) -> List[Dict[str, Any]]:
        """Generates realistic simulated NISAR L-band granules when DAAC is unreachable."""
        results = []
        curr = start_date
        step = datetime.timedelta(days=12)
        
        while curr <= end_date:
            granule_id = f"NISAR_L1_GRD_1SDH_{curr.strftime('%Y%m%d')}T123000_{curr.strftime('%Y%m%d')}T123024_001205_004_001"
            results.append({
                "granule_id": granule_id,
                "acquisition_time": f"{curr.isoformat()}T12:30:00Z",
                "sensor": "NISAR",
                "frequency_band": "L-band",
                "polarizations": ["HH", "HV"],
                "spatial_bounds": [
                    (bbox[0], bbox[1]),
                    (bbox[2], bbox[3])
                ],
                "download_url": f"https://datapool.asf.alaska.edu/NISAR/{granule_id}.zip",
                "status": "simulated"
            })
            curr += step
            
        return results
