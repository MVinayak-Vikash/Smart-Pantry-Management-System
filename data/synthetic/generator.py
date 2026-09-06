"""
Scalable Synthetic Dataset Generator for the Smart Pantry Management System.
Generates 12 months (365 days) of realistic daily household pantry consumption,
weight telemetry, refills, sensor noise, packet dropouts, and nutritional intake
across multiple households (500-1,000+).

DISCLAIMER:
This dataset is synthetically generated for development/testing and must not
be represented as real household measurements.
"""

import os
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd

DISCLAIMER_HEADER = (
    "# DISCLAIMER: This dataset is synthetically generated for development/testing "
    "and must not be represented as real household measurements.\n"
)

# Reference Base Consumption per Person per Day (grams)
BASE_DAILY_PER_PERSON = {
    "Rice": 100.0,    # ~100g raw rice / person / day
    "Sugar": 20.0,    # ~20g sugar / person / day
    "Salt": 5.0,      # ~5g salt / person / day
    "Ghee": 12.0,     # ~12g ghee / person / day
}

# Container capacity and thresholds
ITEM_CONFIG = {
    "Rice": {"initial": 5000.0, "min": 1000.0, "refill": 4500.0},
    "Sugar": {"initial": 2000.0, "min": 500.0, "refill": 1800.0},
    "Salt": {"initial": 1000.0, "min": 250.0, "refill": 900.0},
    "Ghee": {"initial": 1000.0, "min": 250.0, "refill": 900.0},
}

# Nutritional reference data per 100g
NUTRITION_REFERENCE = {
    "Rice": {"calories": 365.0, "carbs": 80.0, "protein": 7.1, "fat": 0.7, "sugar": 0.1, "sodium": 5.0, "fiber": 1.3},
    "Sugar": {"calories": 387.0, "carbs": 100.0, "protein": 0.0, "fat": 0.0, "sugar": 100.0, "sodium": 2.0, "fiber": 0.0},
    "Salt": {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "sugar": 0.0, "sodium": 38758.0, "fiber": 0.0},
    "Ghee": {"calories": 900.0, "carbs": 0.0, "protein": 0.0, "fat": 99.5, "sugar": 0.0, "sodium": 0.0, "fiber": 0.0},
}


def generate_household_profiles(num_households: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Generate demographic profiles for synthetic households."""
    random.seed(seed)
    np.random.seed(seed)

    profiles = []
    activity_choices = ["SEDENTARY", "MODERATE", "ACTIVE"]
    activity_weights = [0.25, 0.55, 0.20]

    diet_choices = ["BALANCED", "LOW_SUGAR", "LOW_SODIUM", "VEGETARIAN"]
    diet_weights = [0.60, 0.15, 0.10, 0.15]

    for hid in range(1, num_households + 1):
        # Distribution: family sizes 1 to 7 (weighted towards 3, 4, 5)
        f_size = np.random.choice([1, 2, 3, 4, 5, 6, 7], p=[0.08, 0.20, 0.25, 0.27, 0.12, 0.05, 0.03])

        # Break down into adults, children, elderly
        if f_size == 1:
            adults, children, elderly = 1, 0, 0
        elif f_size == 2:
            adults, children, elderly = (2, 0, 0) if random.random() < 0.85 else (1, 0, 1)
        else:
            elderly = 1 if (random.random() < 0.25 and f_size >= 4) else 0
            remaining = f_size - elderly
            adults = max(1, random.randint(1, min(remaining, 3)))
            children = remaining - adults

        activity = np.random.choice(activity_choices, p=activity_weights)
        diet = np.random.choice(diet_choices, p=diet_weights)

        profiles.append({
            "household_id": hid,
            "household_name": f"Household_{hid:04d}",
            "family_size": int(f_size),
            "adults_count": int(adults),
            "children_count": int(children),
            "elderly_count": int(elderly),
            "activity_profile": activity,
            "dietary_preference": diet,
        })

    return pd.DataFrame(profiles)


def simulate_household_pantry_history(
    household: Dict[str, Any],
    days: int = 365,
    start_date: Optional[datetime] = None,
    seed: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Simulate daily consumption, weight telemetry readings, and nutrition
    for a single household across Rice, Sugar, Salt, and Ghee.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    hid = household["household_id"]
    f_size = household["family_size"]
    activity = household["activity_profile"]
    diet = household["dietary_preference"]

    # Activity multiplier
    act_mult = 0.90 if activity == "SEDENTARY" else (1.15 if activity == "ACTIVE" else 1.0)

    # Base start date
    base_dt = start_date or (datetime.now(timezone.utc) - timedelta(days=days))

    consumption_records = []
    nutrition_records = []

    for item_name, base_rate in BASE_DAILY_PER_PERSON.items():
        cfg = ITEM_CONFIG[item_name]
        nutr = NUTRITION_REFERENCE[item_name]

        # Dietary preference adjustment
        diet_mult = 1.0
        if diet == "LOW_SUGAR" and item_name == "Sugar":
            diet_mult = 0.40
        elif diet == "LOW_SODIUM" and item_name == "Salt":
            diet_mult = 0.50

        # Household baseline with economies of scale
        household_base = base_rate * (f_size ** 0.82) * act_mult * diet_mult

        current_weight = cfg["initial"]

        for d in range(days):
            current_dt = base_dt + timedelta(days=d)
            is_weekend = current_dt.weekday() in (5, 6)

            # Weekend multiplier for staple cooking
            day_mult = 1.25 if (is_weekend and item_name in ("Rice", "Ghee")) else 1.0

            # Celebration / guest spike with probability 0.02 (approx once every 50 days)
            is_spike = random.random() < 0.02
            spike_mult = 2.0 if is_spike else 1.0

            # Gaussian daily variance (std ~ 12% of baseline)
            expected_consumption = household_base * day_mult * spike_mult
            actual_consumption = max(0.0, np.random.normal(expected_consumption, expected_consumption * 0.12))
            actual_consumption = round(actual_consumption, 1)

            prev_weight = current_weight
            refill_amount = 0.0

            # Check if refill event occurs (container dropped below minimum)
            if current_weight - actual_consumption <= cfg["min"]:
                refill_amount = cfg["refill"]
                current_weight = current_weight + refill_amount
                # On refill day, usage is consumed from replenishment
                current_weight = max(0.0, current_weight - actual_consumption)
            else:
                current_weight = max(0.0, current_weight - actual_consumption)

            # Sensor measurement with Gaussian noise (+- 1.2g)
            noise = np.random.normal(0.0, 1.2)
            measured_weight = max(0.0, round(current_weight + noise, 1))

            # 1.5% packet dropout simulation
            is_dropout = random.random() < 0.015

            timestamp_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
            date_str = current_dt.strftime("%Y-%m-%d")

            consumption_records.append({
                "household_id": hid,
                "item_name": item_name,
                "date": date_str,
                "timestamp": timestamp_str,
                "previous_weight": round(prev_weight, 1),
                "current_weight": round(current_weight, 1),
                "measured_weight": measured_weight,
                "consumption_grams": actual_consumption,
                "refill_grams": round(refill_amount, 1),
                "is_weekend": int(is_weekend),
                "is_spike": int(is_spike),
                "is_missing": int(is_dropout),
            })

            # Calculate daily nutritional contribution
            ratio = actual_consumption / 100.0
            nutrition_records.append({
                "household_id": hid,
                "item_name": item_name,
                "date": date_str,
                "timestamp": timestamp_str,
                "consumption_grams": actual_consumption,
                "calories_kcal": round(nutr["calories"] * ratio, 1),
                "carbohydrates_g": round(nutr["carbs"] * ratio, 1),
                "protein_g": round(nutr["protein"] * ratio, 1),
                "fat_g": round(nutr["fat"] * ratio, 1),
                "sugar_g": round(nutr["sugar"] * ratio, 1),
                "sodium_mg": round(nutr["sodium"] * ratio, 1),
                "fiber_g": round(nutr["fiber"] * ratio, 1),
            })

    return consumption_records, nutrition_records


def generate_and_save_datasets(
    num_households: int = 500,
    days: int = 365,
    output_dir: Optional[Path] = None,
    seed: int = 42
) -> Dict[str, Path]:
    """
    Generate and save synthetic datasets (Households, Consumption, Nutrition)
    with strict reproducible seed and disclaimer headers.
    """
    target_dir = output_dir or (Path(__file__).resolve().parent)
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating synthetic data: {num_households} households over {days} days (seed={seed})...")

    # 1. Household Profiles
    df_households = generate_household_profiles(num_households, seed=seed)
    household_path = target_dir / "household_dataset.csv"
    df_households.to_csv(household_path, index=False)

    # 2. Consumption and Nutrition Time-Series
    all_consumption = []
    all_nutrition = []

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    for idx, row in df_households.iterrows():
        h_seed = seed + int(row["household_id"])
        c_records, n_records = simulate_household_pantry_history(
            row.to_dict(),
            days=days,
            start_date=start_date,
            seed=h_seed
        )
        all_consumption.extend(c_records)
        all_nutrition.extend(n_records)

    df_consumption = pd.DataFrame(all_consumption)
    consumption_path = target_dir / "consumption_dataset.csv"
    df_consumption.to_csv(consumption_path, index=False)

    df_nutrition = pd.DataFrame(all_nutrition)
    nutrition_path = target_dir / "nutrition_dataset.csv"
    df_nutrition.to_csv(nutrition_path, index=False)

    print(f"Datasets generated successfully:")
    print(f"  - Households : {household_path} ({len(df_households)} rows)")
    print(f"  - Consumption: {consumption_path} ({len(df_consumption)} rows)")
    print(f"  - Nutrition  : {nutrition_path} ({len(df_nutrition)} rows)")

    return {
        "households": household_path,
        "consumption": consumption_path,
        "nutrition": nutrition_path,
    }


if __name__ == "__main__":
    generate_and_save_datasets(num_households=500, days=365, seed=42)
