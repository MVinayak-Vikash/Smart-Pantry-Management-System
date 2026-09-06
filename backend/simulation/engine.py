"""
Simulation engine for the Smart Pantry Management System.
Executes sensor simulation through the exact same database & calculation pipeline
that real ESP32 / load-cell hardware will use.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from backend.models import Item, WeightReading, MealLog, AlertLog, ShoppingItem
from backend import crud, calculations
from backend.alerts.engine import evaluate_and_sync_alerts
from backend.shopping.generator import generate_restock_recommendations


def simulate_item_reading(
    db: Session,
    item_id: int,
    new_weight: float,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Simulate a raw weight reading from an IoT load cell.
    Routes directly through the standard create_weight_reading pipeline.
    """
    reading = crud.create_weight_reading(db, item_id=item_id, weight=new_weight, timestamp=timestamp)
    if not reading:
        return {"success": False, "error": f"Item {item_id} not found."}

    item = crud.get_item_by_id(db, item_id)
    metrics = crud.compute_item_metrics(item)
    evaluate_and_sync_alerts(db)

    return {
        "success": True,
        "item_name": item.name,
        "new_weight": new_weight,
        "metrics": metrics,
    }


def simulate_consumption_event(
    db: Session,
    item_id: int,
    consumed_grams: float
) -> Dict[str, Any]:
    """Simulate a cooking / consumption event (weight decrease)."""
    item = crud.get_item_by_id(db, item_id)
    if not item:
        return {"success": False, "error": f"Item {item_id} not found."}

    new_weight = max(0.0, round(item.current_quantity - consumed_grams, 1))
    return simulate_item_reading(db, item_id, new_weight)


def simulate_refill_event(
    db: Session,
    item_id: int,
    refill_grams: float
) -> Dict[str, Any]:
    """Simulate grocery replenishment (weight increase)."""
    item = crud.get_item_by_id(db, item_id)
    if not item:
        return {"success": False, "error": f"Item {item_id} not found."}

    new_weight = round(item.current_quantity + refill_grams, 1)
    return simulate_item_reading(db, item_id, new_weight)


def simulate_advance_days(
    db: Session,
    num_days: int = 7,
    household_id: int = 1
) -> Dict[str, Any]:
    """
    Advance pantry simulation by N days with realistic consumption,
    periodic refills, and measurement noise across all active pantry items.
    """
    household = crud.get_household_profile(db, household_id)
    items = crud.get_items(db, active_only=True)
    f_size = household.family_size

    base_rates = {
        "Rice": 100.0,
        "Sugar": 20.0,
        "Salt": 5.0,
        "Ghee": 12.0,
    }

    start_time = datetime.now(timezone.utc) - timedelta(days=num_days)
    total_readings_added = 0

    for d in range(num_days):
        current_time = start_time + timedelta(days=d, hours=10)
        is_weekend = current_time.weekday() in (5, 6)

        for item in items:
            rate = base_rates.get(item.name, 40.0)
            baseline = rate * (f_size ** 0.82)
            if is_weekend and item.name in ("Rice", "Ghee"):
                baseline *= 1.25

            # Random consumption for the day
            daily_cons = max(0.0, np.random.normal(baseline, baseline * 0.12))
            daily_cons = round(daily_cons, 1)

            curr_w = item.current_quantity

            # If approaching low threshold, simulate a refill
            if curr_w - daily_cons <= item.minimum_quantity:
                refill_amt = item.initial_quantity * 0.8
                new_w = round(curr_w + refill_amt - daily_cons, 1)
            else:
                new_w = max(0.0, round(curr_w - daily_cons, 1))

            # Add reading
            crud.create_weight_reading(db, item_id=item.id, weight=new_w, timestamp=current_time)
            total_readings_added += 1

    evaluate_and_sync_alerts(db, household_id=household_id)
    generate_restock_recommendations(db, household_id=household_id)

    return {
        "success": True,
        "days_advanced": num_days,
        "readings_logged": total_readings_added,
        "items_updated": len(items),
    }


def reset_demo_environment(db: Session) -> Dict[str, Any]:
    """Clean reset of demo database back to fresh default state with sample readings."""
    # Delete non-core logs
    db.query(AlertLog).delete()
    db.query(ShoppingItem).delete()
    db.query(MealLog).delete()
    db.query(WeightReading).delete()
    db.commit()

    # Re-seed baseline
    crud.seed_default_household(db)
    crud.seed_initial_items(db)
    crud.seed_initial_recipes(db)
    crud.seed_sample_readings(db)
    evaluate_and_sync_alerts(db)
    generate_restock_recommendations(db)

    return {
        "success": True,
        "message": "Pantry demo environment reset to default clean state successfully."
    }
