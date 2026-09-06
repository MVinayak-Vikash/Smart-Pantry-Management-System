import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.calculations import (
    calculate_nutritional_intake,
    combine_pantry_and_manual_nutrition,
    classify_dietary_pattern,
)
from backend import crud, models


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    crud.seed_default_household(db)
    yield db
    db.close()


def test_calculate_nutritional_intake_rice():
    """Rice 200g should give: 730 kcal, 160g carbs, 14.2g protein, 1.4g fat, 0.2g sugar, 10mg sodium, 2.6g fiber."""
    rice_profile = {
        "calories_per_100g": 365.0,
        "carbohydrates_per_100g": 80.0,
        "protein_per_100g": 7.1,
        "fat_per_100g": 0.7,
        "sugar_per_100g": 0.1,
        "sodium_mg_per_100g": 5.0,
        "fiber_per_100g": 1.3,
    }
    intake = calculate_nutritional_intake(200.0, rice_profile)
    assert intake["calories_kcal"] == 730.0
    assert intake["carbohydrates_g"] == 160.0
    assert intake["protein_g"] == 14.2
    assert intake["fat_g"] == 1.4
    assert intake["sugar_g"] == 0.2
    assert intake["sodium_mg"] == 10.0
    assert intake["fiber_g"] == 2.6


def test_calculate_nutritional_intake_zero_or_negative():
    """Zero or negative consumption should return 0 for all nutrients."""
    rice_profile = {"calories_per_100g": 365.0}
    intake_zero = calculate_nutritional_intake(0.0, rice_profile)
    assert intake_zero["calories_kcal"] == 0.0

    intake_neg = calculate_nutritional_intake(-50.0, rice_profile)
    assert intake_neg["calories_kcal"] == 0.0


def test_combine_pantry_and_manual_nutrition():
    """Pantry intake and manual meal logs must be cleanly separate with accurate combined total."""
    pantry_totals = {
        "calories_kcal": 500.0,
        "carbohydrates_g": 100.0,
        "protein_g": 10.0,
        "fat_g": 5.0,
        "sugar_g": 15.0,
        "sodium_mg": 400.0,
        "fiber_g": 2.0,
    }

    class MockMeal:
        calories = 350.0
        carbohydrates = 40.0
        protein = 20.0
        fat = 12.0
        sugar = 5.0
        sodium = 300.0
        fiber = 3.0

    combined = combine_pantry_and_manual_nutrition(pantry_totals, [MockMeal(), MockMeal()])

    # Check pantry subtotal
    assert combined["tracked_pantry"]["calories_kcal"] == 500.0
    # Check manual subtotal (350 * 2 = 700)
    assert combined["manual_logged"]["calories_kcal"] == 700.0
    assert combined["manual_logged"]["protein_g"] == 40.0
    # Check combined total (500 + 700 = 1200)
    assert combined["total_combined"]["calories_kcal"] == 1200.0
    assert combined["total_combined"]["protein_g"] == 50.0


def test_classify_dietary_pattern():
    """Test deterministic pattern classification and insufficient data guard."""
    # 1. Insufficient data (< 3 days)
    p, desc = classify_dietary_pattern(sugar_avg_daily=80.0, sodium_avg_daily=3000.0, fat_avg_daily=70.0, days_with_data=2)
    assert p == "INSUFFICIENT_DATA"

    # 2. High sugar (> 50g)
    p, desc = classify_dietary_pattern(sugar_avg_daily=55.0, sodium_avg_daily=800.0, fat_avg_daily=20.0, days_with_data=5)
    assert p == "HIGH_SUGAR"

    # 3. High sodium (> 2000mg)
    p, desc = classify_dietary_pattern(sugar_avg_daily=20.0, sodium_avg_daily=2500.0, fat_avg_daily=20.0, days_with_data=5)
    assert p == "HIGH_SODIUM"

    # 4. High fat (> 60g)
    p, desc = classify_dietary_pattern(sugar_avg_daily=20.0, sodium_avg_daily=800.0, fat_avg_daily=65.0, days_with_data=5)
    assert p == "HIGH_FAT"

    # 5. Increasing consumption trend (+30%)
    p, desc = classify_dietary_pattern(sugar_avg_daily=20.0, sodium_avg_daily=800.0, fat_avg_daily=20.0, trend_7d_vs_30d=1.45, days_with_data=10)
    assert p == "INCREASING_CONSUMPTION"

    # 6. Normal
    p, desc = classify_dietary_pattern(sugar_avg_daily=25.0, sodium_avg_daily=1000.0, fat_avg_daily=25.0, trend_7d_vs_30d=1.05, cv_daily=0.3, days_with_data=10)
    assert p == "NORMAL"


def test_meal_log_crud(db_session):
    """Test manual meal logging and retrieval."""
    meal = crud.create_meal_log(
        db_session,
        meal_data={
            "meal_name": "Vegetable Biryani Lunch",
            "description": "Ate outside at office canteen",
            "calories": 480.0,
            "carbohydrates": 65.0,
            "protein": 12.0,
            "fat": 18.0,
            "sugar": 3.0,
            "sodium": 650.0,
            "fiber": 4.5,
        },
        household_id=1
    )
    assert meal.id is not None
    assert meal.meal_name == "Vegetable Biryani Lunch"

    logs = crud.get_meal_logs(db_session, household_id=1)
    assert len(logs) == 1
    assert logs[0].calories == 480.0
