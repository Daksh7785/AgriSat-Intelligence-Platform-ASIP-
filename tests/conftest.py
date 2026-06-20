import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import sys
import os

# Include backend path in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import get_db

@pytest.fixture
def mock_db():
    session = MagicMock()
    return session

@pytest.fixture
def client(mock_db):
    # Override get_db dependency to supply our mock session
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
