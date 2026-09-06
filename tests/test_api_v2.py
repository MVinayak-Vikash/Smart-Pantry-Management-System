import pytest
from datetime import datetime, timezone
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


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Create fresh tables and seed base entities before each test."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    crud.seed_default_household(db)
    crud.seed_initial_items(db)
    crud.seed_initial_recipes(db)
    crud.seed_sample_readings(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_household_endpoints():
    """GET and PUT /household."""
    res = client.get("/household")
    assert res.status_code == 200
    data = res.json()
    assert data["family_size"] == 4

    # Update household
    put_res = client.put("/household", json={
        "household_name": "Patel Household",
        "family_size": 5,
        "adults_count": 2,
        "children_count": 2,
        "elderly_count": 1,
        "dietary_preference": "VEGETARIAN"
    })
    assert put_res.status_code == 200
    assert put_res.json()["household_name"] == "Patel Household"
    assert put_res.json()["family_size"] == 5

    # Invalid demographic sum: 2 + 1 + 0 = 3 != 5
    inv_res = client.put("/household", json={
        "family_size": 5,
        "adults_count": 2,
        "children_count": 1,
        "elderly_count": 0,
    })
    assert inv_res.status_code == 422


def test_telemetry_weight_endpoint():
    """POST /telemetry/weight should support hardware-ready payloads."""
    # Rice is item 1
    res = client.post("/telemetry/weight", json={
        "device_id": "ESP32_TEST_SCALE",
        "item_id": 1,
        "weight": 3450.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["current_weight"] == 3450.0
    assert data["item_name"] == "Rice"


def test_predictions_endpoints():
    """GET /predictions and /predictions/{item_id}."""
    res = client.get("/predictions")
    assert res.status_code == 200
    preds = res.json()
    assert len(preds) == 4
    for p in preds:
        assert p["predicted_daily_consumption"] > 0
        assert p["prediction_range_90_low"] <= p["predicted_daily_consumption"]
        assert p["prediction_range_90_high"] >= p["predicted_daily_consumption"]

    res_single = client.get("/predictions/1")
    assert res_single.status_code == 200
    assert res_single.json()["item_name"] == "Rice"


def test_diet_summary_and_trends():
    """GET /diet/summary and GET /diet/trends."""
    summary_res = client.get("/diet/summary?period=today")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "tracked_pantry_intake" in summary
    assert "manual_logged_intake" in summary
    assert "total_combined_intake" in summary
    assert "dietary_pattern" in summary
    assert "lifestyle awareness" in summary["disclaimer"].lower()

    trends_res = client.get("/diet/trends")
    assert trends_res.status_code == 200
    assert isinstance(trends_res.json(), list)


def test_manual_meal_logging_flow():
    """POST /meals and GET /meals."""
    post_res = client.post("/meals", json={
        "meal_name": "Paneer Roll Snack",
        "calories": 320.0,
        "carbohydrates": 35.0,
        "protein": 14.0,
        "fat": 12.0,
        "sugar": 2.0,
        "sodium": 400.0,
        "fiber": 2.5
    })
    assert post_res.status_code == 201
    meal = post_res.json()
    assert meal["meal_name"] == "Paneer Roll Snack"

    get_res = client.get("/meals")
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1


def test_recipes_endpoints():
    """GET /recipes and GET /recipes/recommendations."""
    rec_res = client.get("/recipes")
    assert rec_res.status_code == 200
    assert len(rec_res.json()) >= 5

    recs_res = client.get("/recipes/recommendations")
    assert recs_res.status_code == 200
    data = recs_res.json()
    assert "ready_to_cook" in data
    assert "missing_ingredients" in data
    assert "pantry_clearers" in data
    assert "healthier_alternatives" in data


def test_shopping_list_flow():
    """GET and POST /shopping-list/generate."""
    gen_res = client.post("/shopping-list/generate")
    assert gen_res.status_code == 200

    list_res = client.get("/shopping-list")
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)


def test_alerts_and_resolution_flow():
    """GET /alerts and POST /alerts/{id}/resolve."""
    alerts_res = client.get("/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    if alerts:
        a_id = alerts[0]["id"]
        res_res = client.post(f"/alerts/{a_id}/resolve")
        assert res_res.status_code == 200
        assert res_res.json()["is_resolved"] is True


def test_ml_evaluation_endpoint():
    """GET /ml/evaluation returns benchmark audit data."""
    res = client.get("/ml/evaluation")
    assert res.status_code == 200
    data = res.json()
    assert "regression_benchmarks" in data
    assert len(data["regression_benchmarks"]) >= 3
    assert "feature_importance" in data
    assert "synthetically generated" in data["notice"].lower()


def test_simulation_endpoints():
    """POST /simulation/simulate-reading and /simulation/simulate-days."""
    sim_res = client.post("/simulation/simulate-reading?item_id=1&new_weight=4200")
    assert sim_res.status_code == 200
    assert sim_res.json()["new_weight"] == 4200.0

    days_res = client.post("/simulation/simulate-days?num_days=3")
    assert days_res.status_code == 200
    assert days_res.json()["days_advanced"] == 3
