"""
Pure business logic and calculation module for the Smart Pantry Management System.
All calculations (consumption, refills, intake averages, availability, remaining days,
nutritional estimation, and dietary pattern classification) are isolated here
for testability, maintainability, and clean architecture.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple


def calculate_availability_status(current_quantity: float, minimum_quantity: float) -> str:
    """
    Determine item availability:
    - current_quantity <= 0 -> UNAVAILABLE
    - current_quantity <= minimum_quantity -> LOW
    - otherwise -> AVAILABLE
    """
    if current_quantity <= 0:
        return "UNAVAILABLE"
    if current_quantity <= minimum_quantity:
        return "LOW"
    return "AVAILABLE"


def calculate_consumption_intervals(
    readings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compute consumption and refill intervals for a chronologically ordered list of readings.
    
    Each reading dict should have:
      - 'weight': float
      - 'timestamp': datetime (or ISO string)
      - 'id': Optional[int]

    Returns a list of dicts:
      - 'timestamp': datetime
      - 'previous_weight': float
      - 'current_weight': float
      - 'consumption': float (>= 0)
      - 'refill_amount': float (>= 0)
    """
    if len(readings) < 2:
        return []

    # Sort chronologically by timestamp
    sorted_readings = sorted(readings, key=lambda r: r["timestamp"])
    intervals = []

    for i in range(1, len(sorted_readings)):
        prev_w = float(sorted_readings[i - 1]["weight"])
        curr_w = float(sorted_readings[i]["weight"])
        curr_time = sorted_readings[i]["timestamp"]

        if curr_w < prev_w:
            # Consumption event
            consumption = round(prev_w - curr_w, 2)
            refill = 0.0
        elif curr_w > prev_w:
            # Refill / replenishment event
            consumption = 0.0
            refill = round(curr_w - prev_w, 2)
        else:
            # No change
            consumption = 0.0
            refill = 0.0

        intervals.append({
            "timestamp": curr_time,
            "previous_weight": prev_w,
            "current_weight": curr_w,
            "consumption": consumption,
            "refill_amount": refill,
        })

    return intervals


def calculate_average_daily_intake(
    readings: List[Dict[str, Any]]
) -> Tuple[Optional[float], int]:
    """
    Calculate average daily consumption:
      total consumption / number of days with consumption data

    Returns (average_daily_intake, number_of_days_with_data):
      - average_daily_intake: float (grams/day) rounded to 2 decimal places, or None if insufficient data.
      - number_of_days_with_data: int count of distinct calendar days where consumption occurred.
    """
    intervals = calculate_consumption_intervals(readings)
    if not intervals:
        return None, 0

    total_consumption = 0.0
    days_with_consumption = set()

    for interval in intervals:
        cons = interval["consumption"]
        if cons > 0:
            total_consumption += cons
            ts = interval["timestamp"]
            if isinstance(ts, str):
                day_val = ts[:10]
            elif isinstance(ts, (datetime, date)):
                day_val = ts.strftime("%Y-%m-%d")
            else:
                day_val = str(ts)
            days_with_consumption.add(day_val)

    num_days = len(days_with_consumption)
    if num_days == 0 or total_consumption <= 0:
        return None, 0

    avg_intake = round(total_consumption / num_days, 2)
    return avg_intake, num_days


def calculate_intake_status(
    average_daily_intake: Optional[float],
    high_intake_threshold: float
) -> str:
    """
    Compare average daily intake against high_intake_threshold:
    - If average_daily_intake is None (insufficient data) -> INSUFFICIENT DATA
    - If average_daily_intake > high_intake_threshold -> HIGH
    - Otherwise -> NORMAL
    """
    if average_daily_intake is None:
        return "INSUFFICIENT DATA"
    if average_daily_intake > high_intake_threshold:
        return "HIGH"
    return "NORMAL"


def calculate_remaining_days(
    current_quantity: float,
    average_daily_intake: Optional[float]
) -> Optional[float]:
    """
    Estimate remaining days of pantry supply:
    If current_quantity > 0 and average_daily_intake > 0:
      remaining_days = round(current_quantity / average_daily_intake, 1)
    Otherwise:
      None (insufficient data)
    """
    if average_daily_intake is None or average_daily_intake <= 0 or current_quantity <= 0:
        return None
    return round(current_quantity / average_daily_intake, 1)


# ===================================================
# NUTRITION & CALORIE CALCULATIONS
# ===================================================

def calculate_nutritional_intake(
    consumed_grams: float,
    nutrition_profile: Dict[str, float]
) -> Dict[str, float]:
    """
    Compute nutritional intake from consumed grams of a food item.
    Formula: nutrient_intake = consumed_grams * nutrient_per_100g / 100

    Guards against negative values.
    """
    if consumed_grams <= 0:
        return {
            "calories_kcal": 0.0,
            "carbohydrates_g": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "sugar_g": 0.0,
            "sodium_mg": 0.0,
            "fiber_g": 0.0,
        }

    ratio = consumed_grams / 100.0
    return {
        "calories_kcal": round(max(0.0, float(nutrition_profile.get("calories_per_100g", 0.0)) * ratio), 1),
        "carbohydrates_g": round(max(0.0, float(nutrition_profile.get("carbohydrates_per_100g", 0.0)) * ratio), 1),
        "protein_g": round(max(0.0, float(nutrition_profile.get("protein_per_100g", 0.0)) * ratio), 1),
        "fat_g": round(max(0.0, float(nutrition_profile.get("fat_per_100g", 0.0)) * ratio), 1),
        "sugar_g": round(max(0.0, float(nutrition_profile.get("sugar_per_100g", 0.0)) * ratio), 1),
        "sodium_mg": round(max(0.0, float(nutrition_profile.get("sodium_mg_per_100g", 0.0)) * ratio), 1),
        "fiber_g": round(max(0.0, float(nutrition_profile.get("fiber_per_100g", 0.0)) * ratio), 1),
    }


def aggregate_pantry_nutrition_by_day(
    items_consumption_history: List[Dict[str, Any]],
    items_map: Dict[int, Any]
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate daily nutritional intake across all pantry items based on consumption records.
    Returns a dict keyed by date ('YYYY-MM-DD') with total nutrients for that day.
    """
    daily_totals: Dict[str, Dict[str, float]] = {}

    for history in items_consumption_history:
        item_id = history.get("item_id")
        item = items_map.get(item_id)
        if not item:
            continue

        nutr_profile = {
            "calories_per_100g": getattr(item, "calories_per_100g", 0.0),
            "carbohydrates_per_100g": getattr(item, "carbohydrates_per_100g", 0.0),
            "protein_per_100g": getattr(item, "protein_per_100g", 0.0),
            "fat_per_100g": getattr(item, "fat_per_100g", 0.0),
            "sugar_per_100g": getattr(item, "sugar_per_100g", 0.0),
            "sodium_mg_per_100g": getattr(item, "sodium_mg_per_100g", 0.0),
            "fiber_per_100g": getattr(item, "fiber_per_100g", 0.0),
        }

        for record in history.get("records", []):
            cons = record.get("consumption", 0.0)
            if cons <= 0:
                continue

            ts = record.get("timestamp")
            if isinstance(ts, (datetime, date)):
                day_str = ts.strftime("%Y-%m-%d")
            elif isinstance(ts, str):
                day_str = ts[:10]
            else:
                day_str = str(ts)[:10]

            if day_str not in daily_totals:
                daily_totals[day_str] = {
                    "calories_kcal": 0.0,
                    "carbohydrates_g": 0.0,
                    "protein_g": 0.0,
                    "fat_g": 0.0,
                    "sugar_g": 0.0,
                    "sodium_mg": 0.0,
                    "fiber_g": 0.0,
                }

            intake = calculate_nutritional_intake(cons, nutr_profile)
            for k, v in intake.items():
                daily_totals[day_str][k] = round(daily_totals[day_str][k] + v, 1)

    return daily_totals


def combine_pantry_and_manual_nutrition(
    pantry_totals: Dict[str, float],
    manual_meals: List[Any]
) -> Dict[str, Any]:
    """
    Combine tracked pantry nutrition with manually logged external meals.
    Keeps tracked vs manual strictly separated and computes combined total.
    """
    manual_totals = {
        "calories_kcal": 0.0,
        "carbohydrates_g": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 0.0,
        "fiber_g": 0.0,
    }

    for meal in manual_meals:
        manual_totals["calories_kcal"] += getattr(meal, "calories", 0.0)
        manual_totals["carbohydrates_g"] += getattr(meal, "carbohydrates", 0.0)
        manual_totals["protein_g"] += getattr(meal, "protein", 0.0)
        manual_totals["fat_g"] += getattr(meal, "fat", 0.0)
        manual_totals["sugar_g"] += getattr(meal, "sugar", 0.0)
        manual_totals["sodium_mg"] += getattr(meal, "sodium", 0.0)
        manual_totals["fiber_g"] += getattr(meal, "fiber", 0.0)

    for k in manual_totals:
        manual_totals[k] = round(manual_totals[k], 1)

    combined = {}
    for k in manual_totals:
        combined[k] = round(pantry_totals.get(k, 0.0) + manual_totals[k], 1)

    return {
        "tracked_pantry": pantry_totals,
        "manual_logged": manual_totals,
        "total_combined": combined,
    }


# ===================================================
# DIETARY PATTERN CLASSIFICATION
# ===================================================

def classify_dietary_pattern(
    sugar_avg_daily: float,
    sodium_avg_daily: float,
    fat_avg_daily: float,
    trend_7d_vs_30d: Optional[float] = None,
    cv_daily: Optional[float] = None,
    days_with_data: int = 0
) -> Tuple[str, str]:
    """
    Evaluate dietary consumption pattern from tracked foods.
    Deterministic rule engine that prevents label ambiguity.

    Returns:
      (pattern_code, description)
    """
    if days_with_data < 3:
        return (
            "INSUFFICIENT_DATA",
            "Insufficient historical data (< 3 days with consumption) to evaluate dietary pattern."
        )

    # Threshold checks based on WHO / dietary guidelines
    if sugar_avg_daily > 50.0:
        return (
            "HIGH_SUGAR",
            "High sugar intake detected from tracked pantry foods (averaging > 50g/day)."
        )

    if sodium_avg_daily > 2000.0:
        return (
            "HIGH_SODIUM",
            "High sodium intake detected from tracked seasoning (averaging > 2,000mg/day)."
        )

    if fat_avg_daily > 60.0:
        return (
            "HIGH_FAT",
            "High fat consumption detected from tracked pantry staples (averaging > 60g/day)."
        )

    if trend_7d_vs_30d is not None and trend_7d_vs_30d > 1.30:
        return (
            "INCREASING_CONSUMPTION",
            "Recent 7-day consumption is 30% higher than historical 30-day baseline."
        )

    if cv_daily is not None and cv_daily > 0.85:
        return (
            "IRREGULAR",
            "High day-to-day consumption variance observed across tracked items."
        )

    return (
        "NORMAL",
        "Dietary intake from tracked pantry foods is within standard household benchmarks."
    )
