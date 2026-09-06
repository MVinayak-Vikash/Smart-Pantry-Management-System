"""
Deterministic Recipe Recommendation Engine for Smart Pantry Management System.
Evaluates pantry inventory, scales ingredient requirements dynamically by family size,
identifies pantry-clearing opportunities, and recommends healthier alternatives.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models import Recipe, Item, HouseholdProfile
from backend import crud, calculations


def evaluate_recipe_recommendations(
    db: Session,
    household_id: int = 1
) -> Dict[str, Any]:
    """
    Generate inventory-aware, family-size scaled recipe recommendations.
    Returns categorized lists:
      - ready_to_cook
      - missing_ingredients
      - pantry_clearers
      - healthier_alternatives
    """
    household = crud.get_household_profile(db, household_id)
    family_size = max(1, household.family_size)
    diet_pref = household.dietary_preference or "BALANCED"

    # Fetch pantry items and calculate their live remaining days
    items = crud.get_items(db, active_only=True)
    items_map: Dict[str, Item] = {}
    pantry_clearer_item_names = set()

    for item in items:
        items_map[item.name.lower()] = item
        metrics = crud.compute_item_metrics(item)
        rem_days = metrics.get("remaining_days")
        avail = metrics.get("availability_status")
        # Items nearing depletion or at low stock qualify for pantry clearing
        if (rem_days is not None and rem_days <= 5.0) or avail == "LOW":
            pantry_clearer_item_names.add(item.name.lower())

    recipes = crud.get_recipes(db)
    if not recipes:
        crud.seed_initial_recipes(db)
        recipes = crud.get_recipes(db)

    ready_to_cook = []
    missing_ingredients = []
    pantry_clearers = []
    healthier_alternatives = []

    for recipe in recipes:
        base_servings = max(1, recipe.base_servings)
        serving_scale = family_size / base_servings

        scaled_ingredients = []
        can_cook = True
        missing_count = 0
        uses_pantry_clearer = False

        for ing in recipe.ingredients:
            scaled_qty = round(ing.quantity_per_serving * family_size, 1)
            item_key = ing.item_name.lower()
            pantry_item = items_map.get(item_key)

            if pantry_item:
                current_stock = pantry_item.current_quantity
                in_stock = (current_stock >= scaled_qty)
                if not in_stock:
                    can_cook = False
                    missing_count += 1
                if item_key in pantry_clearer_item_names:
                    uses_pantry_clearer = True
            else:
                # External ingredient
                current_stock = None
                in_stock = True

            scaled_ingredients.append({
                "item_name": ing.item_name,
                "item_id": pantry_item.id if pantry_item else None,
                "quantity_per_serving": ing.quantity_per_serving,
                "scaled_quantity": scaled_qty,
                "unit": ing.unit,
                "is_pantry_item": ing.is_pantry_item,
                "current_stock": current_stock,
                "is_in_stock": in_stock,
            })

        tags_list = [t.strip() for t in recipe.tags.split(",") if t.strip()]
        diet_attrs = [d.strip() for d in recipe.dietary_attributes.split(",") if d.strip()]

        total_cal = round(recipe.estimated_calories_per_serving * family_size, 1)

        recipe_dict = {
            "id": recipe.id,
            "name": recipe.name,
            "description": recipe.description,
            "category": recipe.category,
            "prep_time_minutes": recipe.prep_time_minutes,
            "base_servings": base_servings,
            "target_servings": family_size,
            "instructions": recipe.instructions,
            "estimated_calories_per_serving": recipe.estimated_calories_per_serving,
            "total_estimated_calories": total_cal,
            "tags": tags_list,
            "dietary_attributes": diet_attrs,
            "can_cook": can_cook,
            "missing_ingredients_count": missing_count,
            "pantry_clearer": uses_pantry_clearer,
            "ingredients": scaled_ingredients,
        }

        if can_cook:
            ready_to_cook.append(recipe_dict)
        else:
            missing_ingredients.append(recipe_dict)

        if uses_pantry_clearer and can_cook:
            pantry_clearers.append(recipe_dict)

        # Healthier alternatives check
        is_healthy = False
        if diet_pref == "LOW_SUGAR" and any("lower sugar" in t.lower() for t in tags_list):
            is_healthy = True
        elif diet_pref == "LOW_SODIUM" and any("lower sodium" in t.lower() for t in tags_list):
            is_healthy = True
        elif any(t.lower() in ("light", "clean", "recovery", "lower fat", "lower sodium", "lower sugar") for t in tags_list):
            is_healthy = True

        if is_healthy:
            healthier_alternatives.append(recipe_dict)

    return {
        "family_size": family_size,
        "ready_to_cook": ready_to_cook,
        "missing_ingredients": missing_ingredients,
        "pantry_clearers": pantry_clearers,
        "healthier_alternatives": healthier_alternatives,
    }
