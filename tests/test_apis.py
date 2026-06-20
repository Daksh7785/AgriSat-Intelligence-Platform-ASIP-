from unittest.mock import MagicMock
from app.api.auth import get_current_user
from app.db import models
from app.main import app

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_signup(client, mock_db):
    # Mock database checks
    mock_db.query().filter().first.return_value = None
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    
    # Assign side-effect to set ID on refresh
    def mock_refresh(obj):
        obj.id = 1
    mock_db.refresh.side_effect = mock_refresh
    
    payload = {
        "email": "test@agrisense.ai",
        "password": "testpassword",
        "role": "viewer"
    }
    
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 200
    assert response.json()["email"] == "test@agrisense.ai"

def test_copilot_chat(client):
    # Mock current user authentication
    mock_user = models.User(id=1, email="test@agrisense.ai", role="viewer")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    payload = {
        "message": "Show stressed wheat fields"
      }
      
    response = client.post("/api/v1/copilot/query", json=payload)
    assert response.status_code == 200
    assert "intent" in response.json()
    assert response.json()["intent"] == "show_stressed_wheat"
    
    app.dependency_overrides.clear()

def test_stress_reports(client, mock_db):
    # Mock current user authentication
    mock_user = models.User(id=1, email="test@agrisense.ai", role="viewer")
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Mock database group metrics for stress reports
    mock_db.query().join().join().all.return_value = []
    
    response = client.get("/api/v1/stress/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    app.dependency_overrides.clear()
