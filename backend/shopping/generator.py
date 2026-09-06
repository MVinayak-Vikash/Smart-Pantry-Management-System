"""
Smart Grocery & Restock List Engine for Smart Pantry Management System.
Evaluates current stock levels, ML depletion predictions, and 7-day demand
against a Target Stock Level policy to generate prioritized, deduplicated shopping lists.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import Item, ShoppingItem, HouseholdProfile
from backend import crud
from backend.ml.predictor import get_predictor


def calculate_suggested_purchase(
    current_quantity: float,
    initial_quantity: float,
    minimum_quantity: float
) -> float:
    """
    Target Stock Level Policy:
      target_stock_level = max(initial_quantity, minimum_quantity * 3)
      suggested_purchase = max(0, target_stock_level - current_quantity)
    """
    target_stock_level = max(initial_quantity, minimum_quantity * 3.0)
    suggested = max(0.0, target_stock_level - current_quantity)
    return round(suggested, 1)


def generate_restock_recommendations(
    db: Session,
    household_id: int = 1
) -> List[ShoppingItem]:
    """
    Analyze all active pantry items and generate or update pending shopping list entries.
    Prevents duplicate entries by updating existing PENDING records.
    """
    household = crud.get_household_profile(db, household_id)
    items = crud.get_items(db, active_only=True)
    predictor = get_predictor()

    generated_or_updated = []

    for item in items:
        pred_data = predictor.predict_item_consumption(item, household)
        curr_qty = item.current_quantity
        min_qty = item.minimum_quantity
        init_qty = item.initial_quantity
        rem_days = pred_data.get("remaining_days_ml")
        pred_7d = pred_data.get("predicted_7d_consumption", 0.0)

        needs_restock = False
        priority = "MEDIUM"
        reason_parts = []

        # 1. Critical Out of Stock
        if curr_qty <= 0:
            needs_restock = True
            priority = "URGENT"
            reason_parts.append("Container is completely empty")
        # 2. Urgent Depletion (<= 2 days)
        elif rem_days is not None and rem_days <= 2.0:
            needs_restock = True
            priority = "URGENT"
            reason_parts.append(f"Predicted to run out in ~{rem_days} days")
        # 3. Low Stock Threshold
        elif curr_qty <= min_qty:
            needs_restock = True
            priority = "HIGH"
            reason_parts.append(f"Current stock ({curr_qty}g) is below minimum threshold ({min_qty}g)")
        # 4. Predicted runout within 5 days
        elif rem_days is not None and rem_days <= 5.0:
            needs_restock = True
            priority = "HIGH"
            reason_parts.append(f"Predicted stockout in ~{rem_days} days")
        # 5. 7-day projected consumption exceeds current quantity
        elif pred_7d > curr_qty:
            needs_restock = True
            priority = "MEDIUM"
            reason_parts.append(f"7-day expected usage ({pred_7d}g) exceeds stock ({curr_qty}g)")

        if needs_restock:
            suggested_qty = calculate_suggested_purchase(curr_qty, init_qty, min_qty)
            if suggested_qty <= 0:
                suggested_qty = min_qty * 2.0

            reason_str = "; ".join(reason_parts)

            shopping_data = {
                "item_id": item.id,
                "item_name": item.name,
                "current_quantity": curr_qty,
                "suggested_quantity": suggested_qty,
                "unit": item.unit,
                "priority": priority,
                "reason": reason_str,
                "status": "PENDING",
                "predicted_depletion_days": rem_days,
            }

            saved_item = crud.create_or_update_shopping_item(db, shopping_data, household_id=household_id)
            generated_or_updated.append(saved_item)

    return generated_or_updated
