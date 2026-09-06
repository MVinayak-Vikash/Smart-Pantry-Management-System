"""
Smart Pantry Management System - FastAPI Backend Gateway
Exposes REST endpoints for telemetry ingestion, inventory tracking, consumption forecasting,
nutritional estimation, recipe recommendations, smart shopping lists, alerts, and IoT simulation.
"""

import json
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend import database, models, schemas, crud, calculations
from backend.ml.predictor import get_predictor
from backend.ml.pipeline import train_and_evaluate_pipeline
from backend.recipes.engine import evaluate_recipe_recommendations
from backend.shopping.generator import generate_restock_recommendations
from backend.alerts.engine import evaluate_and_sync_alerts
from backend.simulation import engine as sim_engine

MODELS_DIR = Path(__file__).resolve().parent.parent / "data" / "models"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and seed baseline entities."""
    database.init_db()
    yield


app = FastAPI(
    title="Smart Pantry Management System API",
    description=(
        "Full-featured IoT-ready Smart Pantry API for inventory monitoring, "
        "consumption forecasting, nutritional tracking, recipe recommendations, "
        "smart alerts, and sensor simulation. Accepts future ESP32 load-cell telemetry."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for local dashboards and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================================================
# SYSTEM & HEALTH
# ===================================================

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "ok",
        "service": "Smart Pantry Management System",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/seed", tags=["System"])
def seed_sample_data(db: Session = Depends(database.get_db)):
    """
    Seed realistic multi-day sample sensor readings for Rice, Sugar, Salt, and Ghee.
    Preserved from Phase 1.
    """
    result = crud.seed_sample_readings(db)
    evaluate_and_sync_alerts(db)
    generate_restock_recommendations(db)
    return result


# ===================================================
# HOUSEHOLD PROFILE
# ===================================================

@app.get("/household", response_model=schemas.HouseholdProfileResponse, tags=["Household"])
def get_household(db: Session = Depends(database.get_db)):
    """Retrieve the current active household profile."""
    profile = crud.get_household_profile(db, household_id=1)
    return profile


@app.put("/household", response_model=schemas.HouseholdProfileResponse, tags=["Household"])
def update_household(
    payload: schemas.HouseholdProfileUpdate,
    db: Session = Depends(database.get_db)
):
    """Update household name, family size, demographic counts, or preferences."""
    update_data = payload.model_dump(exclude_unset=True)
    profile = crud.update_household_profile(db, update_data, household_id=1)
    return profile


# ===================================================
# PANTRY ITEMS
# ===================================================

@app.get("/items", response_model=List[schemas.ItemSummaryResponse], tags=["Items"])
def get_all_items(db: Session = Depends(database.get_db)):
    """
    Get all pantry items with their current quantity, availability status,
    average daily intake, and intake warning status.
    """
    items = crud.get_items(db, active_only=True)
    results = []
    for item in items:
        metrics = crud.compute_item_metrics(item)
        results.append(schemas.ItemSummaryResponse(**metrics))
    return results


@app.get("/items/{item_id}", response_model=schemas.ItemDetailResponse, tags=["Items"])
def get_item_detail(item_id: int, db: Session = Depends(database.get_db)):
    """
    Get detailed profile of a specific item, including thresholds,
    nutritional facts per 100g, and historical weight readings.
    """
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found."
        )

    metrics = crud.compute_item_metrics(item)
    readings = [
        schemas.WeightReadingResponse(
            id=r.id,
            item_id=r.item_id,
            weight=r.weight,
            timestamp=r.timestamp
        )
        for r in item.readings
    ]

    return schemas.ItemDetailResponse(
        **metrics,
        recent_weight_history=readings
    )


@app.post("/items", response_model=schemas.ItemDetailResponse, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_pantry_item(
    payload: schemas.ItemCreate,
    db: Session = Depends(database.get_db)
):
    """Add a new pantry staple to the inventory."""
    existing = crud.get_item_by_name(db, payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item with name '{payload.name}' already exists."
        )
    item = crud.create_item(db, payload.model_dump())
    metrics = crud.compute_item_metrics(item)
    return schemas.ItemDetailResponse(**metrics, recent_weight_history=[])


@app.put("/items/{item_id}", response_model=schemas.ItemDetailResponse, tags=["Items"])
def update_pantry_item(
    item_id: int,
    payload: schemas.ItemUpdate,
    db: Session = Depends(database.get_db)
):
    """Update item thresholds, storage location, or RFID tag."""
    item = crud.update_item(db, item_id, payload.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found.")
    metrics = crud.compute_item_metrics(item)
    readings = [schemas.WeightReadingResponse.model_validate(r) for r in item.readings]
    return schemas.ItemDetailResponse(**metrics, recent_weight_history=readings)


@app.post("/items/{item_id}/weight", tags=["Weight Ingestion"])
def add_weight_reading(
    item_id: int,
    payload: schemas.WeightReadingCreate,
    db: Session = Depends(database.get_db)
):
    """
    Record a new weight reading (simulated or from ESP32/HX711 load cell).
    Updates item current_quantity, logs reading, and triggers alerts evaluation.
    """
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found."
        )

    reading = crud.create_weight_reading(
        db,
        item_id=item_id,
        weight=payload.weight,
        timestamp=payload.timestamp
    )
    metrics = crud.compute_item_metrics(item)
    evaluate_and_sync_alerts(db)

    return {
        "message": "Weight reading recorded successfully",
        "reading": {
            "id": reading.id,
            "item_id": reading.item_id,
            "weight": reading.weight,
            "timestamp": reading.timestamp,
        },
        "item_status": metrics,
    }


@app.post("/telemetry/weight", tags=["Hardware Telemetry"])
def ingest_telemetry_weight(
    payload: schemas.TelemetryWeightPayload,
    db: Session = Depends(database.get_db)
):
    """
    Hardware-ready telemetry endpoint for physical ESP32 + HX711 + RFID reader.
    Maps RFID UID or item_id to container record.
    """
    target_item = None
    if payload.rfid_uid:
        target_item = crud.get_item_by_rfid(db, payload.rfid_uid)
    elif payload.item_id:
        target_item = crud.get_item_by_id(db, payload.item_id)

    if not target_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No container mapped to RFID '{payload.rfid_uid}' or Item ID {payload.item_id}."
        )

    reading = crud.create_weight_reading(
        db,
        item_id=target_item.id,
        weight=payload.weight,
        timestamp=payload.timestamp
    )
    evaluate_and_sync_alerts(db)
    metrics = crud.compute_item_metrics(target_item)

    return {
        "status": "success",
        "device_id": payload.device_id,
        "item_id": target_item.id,
        "item_name": target_item.name,
        "current_weight": reading.weight,
        "item_status": metrics,
    }


@app.get(
    "/items/{item_id}/consumption",
    response_model=schemas.ConsumptionHistoryResponse,
    tags=["Consumption"]
)
def get_consumption_history(item_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieve historical consumption events and refill amounts.
    Weight decreases are counted as consumption; weight increases are treated as refills.
    """
    history = crud.get_item_consumption_history(db, item_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found."
        )
    return schemas.ConsumptionHistoryResponse(**history)


# ===================================================
# DASHBOARD SUMMARY
# ===================================================

@app.get("/dashboard", response_model=schemas.DashboardSummaryResponse, tags=["Dashboard"])
def get_dashboard_summary(db: Session = Depends(database.get_db)):
    """
    Get aggregated dashboard summary covering pantry items,
    stock alerts, and intake warnings.
    """
    items = crud.get_items(db)
    items_summary = []
    available_count = 0
    low_count = 0
    unavailable_count = 0
    high_intake_count = 0

    for item in items:
        metrics = crud.compute_item_metrics(item)
        summary = schemas.ItemSummaryResponse(**metrics)
        items_summary.append(summary)

        if summary.availability_status == "AVAILABLE":
            available_count += 1
        elif summary.availability_status == "LOW":
            low_count += 1
        elif summary.availability_status == "UNAVAILABLE":
            unavailable_count += 1

        if summary.intake_status == "HIGH":
            high_intake_count += 1

    return schemas.DashboardSummaryResponse(
        items=items_summary,
        total_items=len(items_summary),
        available_count=available_count,
        low_count=low_count,
        unavailable_count=unavailable_count,
        high_intake_count=high_intake_count,
    )


# ===================================================
# PREDICTIONS & FORECASTING
# ===================================================

@app.get("/predictions", response_model=List[schemas.ItemPredictionResponse], tags=["Predictions"])
def get_all_predictions(db: Session = Depends(database.get_db)):
    """
    Retrieve ML-based daily consumption forecast, multi-day projections (7d/14d/30d),
    stock depletion date, and 90% empirical prediction ranges for all pantry items.
    """
    household = crud.get_household_profile(db, household_id=1)
    items = crud.get_items(db, active_only=True)
    predictor = get_predictor()
    results = predictor.predict_all_items(items, household)
    return results


@app.get("/predictions/{item_id}", response_model=schemas.ItemPredictionResponse, tags=["Predictions"])
def get_item_prediction(item_id: int, db: Session = Depends(database.get_db)):
    """Get detailed ML prediction and depletion forecast for a specific item."""
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found.")

    household = crud.get_household_profile(db, household_id=1)
    predictor = get_predictor()
    return predictor.predict_item_consumption(item, household)


# ===================================================
# DIET & NUTRITION
# ===================================================

@app.get("/diet/summary", response_model=schemas.DietSummaryResponse, tags=["Diet & Nutrition"])
def get_diet_summary(
    period: str = Query("today", pattern="^(today|7d|30d)$"),
    db: Session = Depends(database.get_db)
):
    """
    Retrieve estimated calories and macronutrients from tracked pantry foods
    plus manually logged meals, along with dietary pattern classification.
    """
    household = crud.get_household_profile(db, household_id=1)
    items = crud.get_items(db)
    items_map = {i.id: i for i in items}
    items_history = [crud.get_item_consumption_history(db, i.id) for i in items]

    daily_pantry = calculations.aggregate_pantry_nutrition_by_day(items_history, items_map)

    # Date filtering
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    days_to_include = 1 if period == "today" else (7 if period == "7d" else 30)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_to_include)).strftime("%Y-%m-%d")

    # Aggregate pantry totals
    pantry_totals = {
        "calories_kcal": 0.0,
        "carbohydrates_g": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 0.0,
        "fiber_g": 0.0,
    }
    per_item_cal: Dict[str, float] = {}

    for history in items_history:
        item = items_map.get(history["item_id"])
        if not item:
            continue
        item_cal = 0.0
        for r in history.get("records", []):
            if r.get("consumption", 0.0) <= 0:
                continue
            ts = r.get("timestamp")
            d_str = ts.strftime("%Y-%m-%d") if isinstance(ts, (datetime, date)) else str(ts)[:10]
            if period == "today" and d_str != today_str:
                continue
            if period != "today" and d_str < cutoff_date:
                continue
            intake = calculations.calculate_nutritional_intake(
                r["consumption"],
                {
                    "calories_per_100g": item.calories_per_100g,
                    "carbohydrates_per_100g": item.carbohydrates_per_100g,
                    "protein_per_100g": item.protein_per_100g,
                    "fat_per_100g": item.fat_per_100g,
                    "sugar_per_100g": item.sugar_per_100g,
                    "sodium_mg_per_100g": item.sodium_mg_per_100g,
                    "fiber_per_100g": item.fiber_per_100g,
                }
            )
            for k in pantry_totals:
                pantry_totals[k] = round(pantry_totals[k] + intake.get(k, 0.0), 1)
            item_cal += intake.get("calories_kcal", 0.0)

        if item_cal > 0:
            per_item_cal[item.name] = round(item_cal, 1)

    # Fetch manual meals
    manual_meals = crud.get_meal_logs(db, household_id=1, limit=100)
    filtered_meals = []
    for m in manual_meals:
        m_str = m.timestamp.strftime("%Y-%m-%d")
        if period == "today" and m_str != today_str:
            continue
        if period != "today" and m_str < cutoff_date:
            continue
        filtered_meals.append(m)

    combined_dict = calculations.combine_pantry_and_manual_nutrition(pantry_totals, filtered_meals)

    # Dietary Pattern Classification
    days_analyzed = len(daily_pantry)
    sugar_avg = sum(d["sugar_g"] for d in daily_pantry.values()) / max(1, days_analyzed)
    sodium_avg = sum(d["sodium_mg"] for d in daily_pantry.values()) / max(1, days_analyzed)
    fat_avg = sum(d["fat_g"] for d in daily_pantry.values()) / max(1, days_analyzed)

    pattern, desc = calculations.classify_dietary_pattern(
        sugar_avg_daily=sugar_avg,
        sodium_avg_daily=sodium_avg,
        fat_avg_daily=fat_avg,
        days_with_data=days_analyzed
    )

    return schemas.DietSummaryResponse(
        period=period,
        days_analyzed=days_analyzed,
        tracked_pantry_intake=schemas.NutrientBreakdown(**combined_dict["tracked_pantry"]),
        manual_logged_intake=schemas.NutrientBreakdown(**combined_dict["manual_logged"]),
        total_combined_intake=schemas.NutrientBreakdown(**combined_dict["total_combined"]),
        dietary_pattern=pattern,
        dietary_pattern_description=desc,
        per_item_calories=per_item_cal,
    )


@app.get("/diet/trends", response_model=List[schemas.DailyNutritionTrend], tags=["Diet & Nutrition"])
def get_diet_trends(db: Session = Depends(database.get_db)):
    """Retrieve daily time-series of nutritional intake from pantry and logged meals."""
    items = crud.get_items(db)
    items_map = {i.id: i for i in items}
    items_history = [crud.get_item_consumption_history(db, i.id) for i in items]
    daily_pantry = calculations.aggregate_pantry_nutrition_by_day(items_history, items_map)

    trends = []
    for d_str in sorted(daily_pantry.keys()):
        val = daily_pantry[d_str]
        trends.append(schemas.DailyNutritionTrend(
            date=d_str,
            calories=val["calories_kcal"],
            carbohydrates=val["carbohydrates_g"],
            protein=val["protein_g"],
            fat=val["fat_g"],
            sugar=val["sugar_g"],
            sodium=val["sodium_mg"],
            source="tracked_pantry"
        ))
    return trends


@app.post("/meals", response_model=schemas.MealLogResponse, status_code=status.HTTP_201_CREATED, tags=["Meals"])
def log_external_meal(
    payload: schemas.MealLogCreate,
    db: Session = Depends(database.get_db)
):
    """Log a food/meal consumed outside the tracked pantry."""
    meal = crud.create_meal_log(db, payload.model_dump(), household_id=1)
    return meal


@app.get("/meals", response_model=List[schemas.MealLogResponse], tags=["Meals"])
def get_meal_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(database.get_db)
):
    """List recent manually logged meals."""
    return crud.get_meal_logs(db, household_id=1, limit=limit)


# ===================================================
# RECIPES
# ===================================================

@app.get("/recipes", response_model=List[schemas.RecipeResponse], tags=["Recipes"])
def get_recipes_catalog(db: Session = Depends(database.get_db)):
    """Retrieve all recipes scaled to current household family size."""
    recs = evaluate_recipe_recommendations(db, household_id=1)
    all_recipes = recs["ready_to_cook"] + recs["missing_ingredients"]
    return [schemas.RecipeResponse(**r) for r in all_recipes]


@app.get("/recipes/recommendations", response_model=schemas.RecipeRecommendationsResponse, tags=["Recipes"])
def get_recipe_recommendations(db: Session = Depends(database.get_db)):
    """
    Retrieve categorized recipe suggestions:
    - Ready to Cook (100% in stock)
    - Missing Ingredients
    - Pantry Clearers (uses items near depletion)
    - Healthier Alternatives
    """
    recs = evaluate_recipe_recommendations(db, household_id=1)
    return schemas.RecipeRecommendationsResponse(
        family_size=recs["family_size"],
        ready_to_cook=[schemas.RecipeResponse(**r) for r in recs["ready_to_cook"]],
        missing_ingredients=[schemas.RecipeResponse(**r) for r in recs["missing_ingredients"]],
        pantry_clearers=[schemas.RecipeResponse(**r) for r in recs["pantry_clearers"]],
        healthier_alternatives=[schemas.RecipeResponse(**r) for r in recs["healthier_alternatives"]],
    )


# ===================================================
# SHOPPING / GROCERY LIST
# ===================================================

@app.get("/shopping-list", response_model=List[schemas.ShoppingItemResponse], tags=["Shopping List"])
def get_shopping_list(db: Session = Depends(database.get_db)):
    """Retrieve active and suggested restock items."""
    return crud.get_shopping_items(db, household_id=1)


@app.post("/shopping-list/generate", response_model=List[schemas.ShoppingItemResponse], tags=["Shopping List"])
def trigger_shopping_list_generation(db: Session = Depends(database.get_db)):
    """Re-evaluate live stock levels and ML forecasts against Target Stock Level policy."""
    items = generate_restock_recommendations(db, household_id=1)
    return items


@app.post("/shopping-list/{item_id}/purchase", tags=["Shopping List"])
def mark_item_purchased(
    item_id: int,
    record_refill: bool = Query(True),
    db: Session = Depends(database.get_db)
):
    """Mark shopping item as purchased and optionally record refill weight in container."""
    item = crud.mark_shopping_item_purchased(db, shopping_item_id=item_id, record_refill=record_refill)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shopping item {item_id} not found.")
    evaluate_and_sync_alerts(db)
    return {"status": "success", "message": f"Marked '{item.item_name}' as purchased."}


# ===================================================
# ALERTS
# ===================================================

@app.get("/alerts", response_model=List[schemas.AlertLogResponse], tags=["Alerts"])
def get_system_alerts(
    unresolved_only: bool = Query(False),
    db: Session = Depends(database.get_db)
):
    """Retrieve active and historical alerts."""
    evaluate_and_sync_alerts(db, household_id=1)
    return crud.get_alerts(db, household_id=1, unresolved_only=unresolved_only)


@app.post("/alerts/{alert_id}/resolve", response_model=schemas.AlertLogResponse, tags=["Alerts"])
def resolve_alert(alert_id: int, db: Session = Depends(database.get_db)):
    """Mark an active alert as resolved."""
    alert = crud.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found.")
    return alert


# ===================================================
# MACHINE LEARNING EVALUATION
# ===================================================

@app.get("/ml/evaluation", response_model=schemas.MLEvaluationResponse, tags=["Machine Learning"])
def get_ml_evaluation():
    """Retrieve the latest model benchmark metrics comparing ML to moving-average baselines."""
    metrics_path = MODELS_DIR / "model_metrics.json"
    if not metrics_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metrics not found. Please train the ML pipeline first via POST /ml/train."
        )
    with open(metrics_path, "r") as f:
        data = json.load(f)
    return schemas.MLEvaluationResponse(**data)


@app.post("/ml/train", tags=["Machine Learning"])
def trigger_ml_training():
    """Trigger ML model training and chronological evaluation on synthetic dataset."""
    try:
        report = train_and_evaluate_pipeline()
        get_predictor()._load_artifacts()
        return {
            "status": "success",
            "message": "Models trained and evaluated successfully.",
            "trained_at": report.get("trained_at"),
            "benchmarks_count": len(report.get("regression_benchmarks", []))
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ===================================================
# SIMULATION TEST BENCH
# ===================================================

@app.post("/simulation/simulate-reading", tags=["Simulation"])
def simulate_reading(
    item_id: int,
    new_weight: float = Query(..., ge=0),
    db: Session = Depends(database.get_db)
):
    """Simulate a weight reading from an IoT load cell."""
    res = sim_engine.simulate_item_reading(db, item_id, new_weight)
    if not res["success"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res


@app.post("/simulation/simulate-days", tags=["Simulation"])
def simulate_days(
    num_days: int = Query(7, ge=1, le=60),
    db: Session = Depends(database.get_db)
):
    """Advance simulation timeline by N days with realistic consumption and noise."""
    res = sim_engine.simulate_advance_days(db, num_days=num_days, household_id=1)
    return res


@app.post("/simulation/reset", tags=["Simulation"])
def reset_demo_environment(db: Session = Depends(database.get_db)):
    """Reset the demo database back to default clean sample state."""
    res = sim_engine.reset_demo_environment(db)
    return res
