import pytest
import datetime
from unittest.mock import MagicMock, patch

from app.data.nisar_connector import NISARConnector
from app.data.sample_data_generator import generate_sample_data_for_bbox
from app.services.onboarding_service import OnboardingService

@pytest.mark.anyio
async def test_nisar_connector_query():
    connector = NISARConnector()
    bbox = [75.0, 30.0, 75.2, 30.2]
    start_date = datetime.date(2026, 6, 1)
    end_date = datetime.date(2026, 6, 15)
    
    # Verify CMR URL query string compilation
    query_url = connector.build_cmr_query(bbox, start_date, end_date)
    assert "cmr.earthdata.nasa.gov" in query_url
    assert "75.0" in query_url
    assert "30.0" in query_url
    assert "ASF" in query_url
    
    # Verify fallback simulated behavior
    res = await connector.query_asf_daac_metadata(bbox, start_date, end_date)
    assert len(res) >= 1
    assert res[0]["sensor"] == "NISAR"
    assert "L-band" in res[0]["frequency_band"]
    assert "HH" in res[0]["polarizations"]

@pytest.mark.anyio
async def test_generate_sample_data():
    mock_db = MagicMock()
    bbox = [75.0, 30.0, 75.2, 30.2]
    crops = ["wheat", "rice"]
    
    # Verify fields generation in the grid
    fields = await generate_sample_data_for_bbox(
        bbox=bbox,
        crops=crops,
        command_area_id=1,
        season_label="Kharif 2026",
        db=mock_db
    )
    
    assert len(fields) == 4
    assert fields[0].name.startswith("Onboarded Field")
    assert mock_db.add.called

@pytest.mark.anyio
async def test_onboarding_service():
    mock_db = MagicMock()
    service = OnboardingService(mock_db)
    bbox = [75.0, 30.0, 75.2, 30.2]
    crops = ["wheat", "rice"]
    
    # Mock IngestionService so we don't write actual GeoTIFFs to disk during tests
    with patch("app.services.onboarding_service.IngestionService.trigger_temporal_ingestion") as mock_ingest:
        result = await service.onboard_command_area(
            name="New Punjab Command",
            bbox=bbox,
            crops=crops,
            capacity_cusec=1500.0,
            season_label="Rabi 2026"
        )
        
        assert result["status"] == "success"
        assert result["fields_created"] == 4
        assert result["name"] == "New Punjab Command"
        assert mock_ingest.called

def test_onboarding_api_endpoint(client, mock_db):
    payload = {
        "name": "Test Command Area",
        "bbox": [75.1, 30.1, 75.3, 30.3],
        "crops": ["wheat", "rice"],
        "capacity_cusec": 1100.0,
        "season_label": "Kharif 2026"
    }
    
    # Mock IngestionService trigger inside the service context
    with patch("app.services.onboarding_service.IngestionService.trigger_temporal_ingestion"):
        response = client.post("/api/v1/onboarding/new-command-area", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["name"] == "Test Command Area"
        assert data["fields_created"] == 4
