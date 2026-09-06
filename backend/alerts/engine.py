"""
Smart Alert Engine for the Smart Pantry Management System.
Monitors stock levels, depletion countdowns, intake thresholds, ML anomalies,
and dietary patterns. Enforces stateful 24-hour deduplication to prevent notification spam.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import Item, AlertLog, HouseholdProfile
from backend import crud, calculations
from backend.ml.predictor import get_predictor


def evaluate_and_sync_alerts(
    db: Session,
    household_id: int = 1
) -> List[AlertLog]:
    """
    Scan all active items and dietary metrics to generate alerts with 24-hour deduplication.
    Returns list of all active (unresolved) alerts for the household.
    """
    household = crud.get_household_profile(db, household_id)
    items = crud.get_items(db, active_only=True)
    predictor = get_predictor()

    generated_alerts = []

    # 1. Evaluate Item Stock & Intake Alerts
    for item in items:
        metrics = crud.compute_item_metrics(item)
        pred_data = predictor.predict_item_consumption(item, household)

        curr_qty = item.current_quantity
        min_qty = item.minimum_quantity
        rem_days_ml = pred_data.get("remaining_days_ml")
        intake_status = metrics.get("intake_status")

        # OUT_OF_STOCK (Critical)
        if curr_qty <= 0:
            a = crud.create_alert_deduplicated(
                db,
                data={
                    "item_id": item.id,
                    "item_name": item.name,
                    "alert_type": "OUT_OF_STOCK",
                    "severity": "CRITICAL",
                    "message": f"CRITICAL: {item.name} is completely out of stock! Refill required immediately.",
                },
                household_id=household_id
            )
            if a:
                generated_alerts.append(a)

        # LOW_STOCK (Warning)
        elif curr_qty <= min_qty:
            a = crud.create_alert_deduplicated(
                db,
                data={
                    "item_id": item.id,
                    "item_name": item.name,
                    "alert_type": "LOW_STOCK",
                    "severity": "WARNING",
                    "message": f"LOW STOCK: {item.name} is at {curr_qty}g (below minimum threshold of {min_qty}g).",
                },
                household_id=household_id
            )
            if a:
                generated_alerts.append(a)

        # PREDICTED_STOCKOUT (Warning)
        if rem_days_ml is not None and rem_days_ml <= 3.0 and curr_qty > 0:
            a = crud.create_alert_deduplicated(
                db,
                data={
                    "item_id": item.id,
                    "item_name": item.name,
                    "alert_type": "PREDICTED_STOCKOUT",
                    "severity": "WARNING",
                    "message": f"DEPLETION WARNING: {item.name} is projected to run out in ~{rem_days_ml} days.",
                },
                household_id=household_id
            )
            if a:
                generated_alerts.append(a)

        # HIGH_CONSUMPTION (Warning)
        if intake_status == "HIGH":
            avg_intake = metrics.get("average_daily_intake", 0.0)
            threshold = item.high_intake_threshold
            a = crud.create_alert_deduplicated(
                db,
                data={
                    "item_id": item.id,
                    "item_name": item.name,
                    "alert_type": "HIGH_CONSUMPTION",
                    "severity": "WARNING",
                    "message": f"HIGH INTAKE: Daily consumption of {item.name} ({avg_intake}g/day) exceeds high limit ({threshold}g/day).",
                },
                household_id=household_id
            )
            if a:
                generated_alerts.append(a)

    # 2. Evaluate Dietary Pattern Alerts
    # Compute aggregate pantry nutrition
    items_history = [crud.get_item_consumption_history(db, i.id) for i in items]
    items_map = {i.id: i for i in items}
    daily_nutr = calculations.aggregate_pantry_nutrition_by_day(items_history, items_map)

    if daily_nutr and len(daily_nutr) >= 3:
        sugar_vals = [d["sugar_g"] for d in daily_nutr.values()]
        sodium_vals = [d["sodium_mg"] for d in daily_nutr.values()]
        fat_vals = [d["fat_g"] for d in daily_nutr.values()]

        avg_sugar = sum(sugar_vals) / len(sugar_vals)
        avg_sodium = sum(sodium_vals) / len(sodium_vals)
        avg_fat = sum(fat_vals) / len(fat_vals)

        pattern, description = calculations.classify_dietary_pattern(
            sugar_avg_daily=avg_sugar,
            sodium_avg_daily=avg_sodium,
            fat_avg_daily=avg_fat,
            days_with_data=len(daily_nutr)
        )

        if pattern == "HIGH_SUGAR":
            crud.create_alert_deduplicated(
                db,
                data={
                    "item_id": None,
                    "item_name": "Pantry Diet",
                    "alert_type": "HIGH_SUGAR_PATTERN",
                    "severity": "INFO",
                    "message": f"DIETARY NOTICE: {description}",
                },
                household_id=household_id
            )
        elif pattern == "HIGH_SODIUM":
            crud.create_alert_deduplicated(
                db,
                data={
                    "item_id": None,
                    "item_name": "Pantry Diet",
                    "alert_type": "HIGH_SALT_PATTERN",
                    "severity": "INFO",
                    "message": f"DIETARY NOTICE: {description}",
                },
                household_id=household_id
            )
        elif pattern == "HIGH_FAT":
            crud.create_alert_deduplicated(
                db,
                data={
                    "item_id": None,
                    "item_name": "Pantry Diet",
                    "alert_type": "HIGH_FAT_PATTERN",
                    "severity": "INFO",
                    "message": f"DIETARY NOTICE: {description}",
                },
                household_id=household_id
            )

    return crud.get_alerts(db, household_id=household_id, unresolved_only=True)
