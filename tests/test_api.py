"""
Integration and functional tests for the Smart Pantry Management System FastAPI endpoints.
Tests:
- Database initialization and default item seeding
- GET /items
- GET /items/{item_id}
- POST /items/{item_id}/weight (valid, negative weight 422, non-existent 404)
- GET /items/{item_id}/consumption
- GET /dashboard
- Status updates (AVAILABLE, LOW, UNAVAILABLE)
- Intake warnings (NORMAL, HIGH, INSUFFICIENT DATA)
- Refill calculation flow
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend import crud, models

# In-memory SQLite for isolated test execution
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Create fresh tables and seed base items before each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    crud.seed_initial_items(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def test_initial_items_seeded():
    """Rice, Sugar, Salt, Ghee must be present with default values."""
    response = client.get("/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 4
    names = [i["name"] for i in items]
    assert "Rice" in names
    assert "Sugar" in names
    assert "Salt" in names
    assert "Ghee" in names

    rice = next(i for i in items if i["name"] == "Rice")
    assert rice["current_quantity"] == 5000.0
    assert rice["minimum_quantity"] == 1000.0
    assert rice["high_intake_threshold"] == 300.0
    assert rice["availability_status"] == "AVAILABLE"
    # No readings yet -> intake status is INSUFFICIENT DATA
    assert rice["intake_status"] == "INSUFFICIENT DATA"
    assert rice["average_daily_intake"] is None
    assert rice["remaining_days"] is None


def test_get_item_by_id():
    """Test retrieving item 1 (Rice)."""
    response = client.get("/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Rice"
    assert data["unit"] == "g"
    assert "recent_weight_history" in data


def test_get_nonexistent_item_returns_404():
    """Requesting an invalid item ID returns 404 Not Found."""
    response = client.get("/items/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_add_weight_reading():
    """POST /items/{item_id}/weight records reading and updates quantity."""
    response = client.post("/items/1/weight", json={"weight": 4800.0})
    assert response.status_code == 200
    body = response.json()
    assert body["reading"]["weight"] == 4800.0
    assert body["reading"]["item_id"] == 1
    assert body["item_status"]["current_quantity"] == 4800.0


def test_add_negative_weight_rejected():
    """Negative weights must be rejected with 422 Unprocessable Entity."""
    response = client.post("/items/1/weight", json={"weight": -100.0})
    assert response.status_code == 422


def test_add_weight_to_invalid_item_returns_404():
    """Adding weight to a non-existent item returns 404."""
    response = client.post("/items/999/weight", json={"weight": 1000.0})
    assert response.status_code == 404


def test_availability_status_transitions():
    """Verify AVAILABLE -> LOW -> UNAVAILABLE as weight decreases."""
    # Rice: minimum_quantity = 1000
    # Quantity 1500 -> AVAILABLE
    client.post("/items/1/weight", json={"weight": 1500.0})
    res = client.get("/items/1").json()
    assert res["availability_status"] == "AVAILABLE"

    # Quantity 900 -> LOW
    client.post("/items/1/weight", json={"weight": 900.0})
    res = client.get("/items/1").json()
    assert res["availability_status"] == "LOW"

    # Quantity 0 -> UNAVAILABLE
    client.post("/items/1/weight", json={"weight": 0.0})
    res = client.get("/items/1").json()
    assert res["availability_status"] == "UNAVAILABLE"


def test_consumption_and_refill_tracking():
    """
    Test reading sequence:
    Day 1: 5000
    Day 2: 4500 (consumption: 500)
    Day 3: 7000 (refill: 2500)
    Day 4: 6800 (consumption: 200)
    """
    db = TestingSessionLocal()
    item = db.query(models.Item).filter(models.Item.id == 1).first()

    base_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    readings = [
        models.WeightReading(item_id=1, weight=5000.0, timestamp=base_time),
        models.WeightReading(item_id=1, weight=4500.0, timestamp=base_time + timedelta(days=1)),
        models.WeightReading(item_id=1, weight=7000.0, timestamp=base_time + timedelta(days=2)),
        models.WeightReading(item_id=1, weight=6800.0, timestamp=base_time + timedelta(days=3)),
    ]
    for r in readings:
        db.add(r)
    item.current_quantity = 6800.0
    db.commit()
    db.close()

    response = client.get("/items/1/consumption")
    assert response.status_code == 200
    data = response.json()

    assert data["total_consumption"] == 700.0
    assert data["total_refill"] == 2500.0
    assert len(data["records"]) == 3
    assert data["days_with_data"] == 2
    # 700 / 2 days = 350 g/day
    assert data["average_daily_intake"] == 350.0

    # Rice threshold is 300 g/day, 350 > 300 -> HIGH intake!
    item_res = client.get("/items/1").json()
    assert item_res["intake_status"] == "HIGH"
    # Remaining days: 6800 / 350 ~ 19.4 days
    assert item_res["remaining_days"] == 19.4


def test_dashboard_endpoint():
    """GET /dashboard should aggregate all items and status counters."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 4
    assert len(data["items"]) == 4
    assert "available_count" in data
    assert "low_count" in data
    assert "unavailable_count" in data
    assert "high_intake_count" in data


def test_seed_sample_data_endpoint():
    """POST /seed endpoint should populate sample readings."""
    response = client.post("/seed")
    assert response.status_code == 200
    assert response.json()["readings_count"] > 0

    # Salt has threshold 5g/day, sample data has 10g/day drop -> HIGH
    salt_res = client.get("/items/3").json()
    assert salt_res["name"] == "Salt"
    assert salt_res["current_quantity"] == 960.0
    assert salt_res["intake_status"] == "HIGH"
    assert salt_res["average_daily_intake"] == 10.0
