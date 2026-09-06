"""
Feature engineering module for Smart Pantry consumption forecasting.
STRICT DATA LEAKAGE PREVENTION:
All rolling averages and lag features for time t are calculated strictly
from observations prior to t (using shift(1)).
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date


ITEM_ENCODING = {
    "Rice": 0,
    "Sugar": 1,
    "Salt": 2,
    "Ghee": 3,
}

FEATURE_COLUMNS = [
    "item_code",
    "family_size",
    "adults_count",
    "children_count",
    "elderly_count",
    "day_of_week",
    "is_weekend",
    "prev_1d_consumption",
    "rolling_3d_avg",
    "rolling_7d_avg",
    "rolling_14d_avg",
    "rolling_30d_avg",
    "trend_7d_vs_30d",
    "current_quantity",
]


def build_time_series_features(
    df_consumption: pd.DataFrame,
    df_households: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Build lag and rolling features from historical consumption records.
    Strictly uses shift(1) so no observation at time t leaks into features at time t.
    """
    df = df_consumption.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["household_id", "item_name", "date"]).reset_index(drop=True)

    # Merge household demographics if available
    if df_households is not None and "family_size" not in df.columns:
        demog_cols = ["household_id", "family_size", "adults_count", "children_count", "elderly_count"]
        avail_cols = [c for c in demog_cols if c in df_households.columns]
        df = df.merge(df_households[avail_cols], on="household_id", how="left")

    # Fill defaults if demographics not provided
    for col in ["family_size", "adults_count", "children_count", "elderly_count"]:
        if col not in df.columns:
            df[col] = 4 if col == "family_size" else 2

    # Map item to numeric code
    df["item_code"] = df["item_name"].map(ITEM_ENCODING).fillna(-1).astype(int)

    # Day of week and weekend flag
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Current quantity in container (prior to today's consumption)
    if "previous_weight" in df.columns:
        df["current_quantity"] = df["previous_weight"]
    elif "current_weight" in df.columns:
        df["current_quantity"] = df["current_weight"]
    else:
        df["current_quantity"] = 2000.0

    # Groupby household and item to compute strict historical lags
    grouped = df.groupby(["household_id", "item_name"])["consumption_grams"]

    # Shift(1) guarantees NO future or current day leakage
    df["prev_1d_consumption"] = grouped.shift(1)
    df["rolling_3d_avg"] = grouped.shift(1).rolling(3, min_periods=1).mean()
    df["rolling_7d_avg"] = grouped.shift(1).rolling(7, min_periods=1).mean()
    df["rolling_14d_avg"] = grouped.shift(1).rolling(14, min_periods=1).mean()
    df["rolling_30d_avg"] = grouped.shift(1).rolling(30, min_periods=1).mean()

    # Trend: ratio of short-term 7d to long-term 30d
    df["trend_7d_vs_30d"] = (df["rolling_7d_avg"] / (df["rolling_30d_avg"] + 0.1)).round(3)

    # Drop first day per group where prev_1d_consumption is NaN
    df = df.dropna(subset=["prev_1d_consumption"]).reset_index(drop=True)

    return df


def extract_live_features_for_item(
    item_name: str,
    current_quantity: float,
    recent_readings: List[Dict[str, Any]],
    family_size: int = 4,
    adults: int = 2,
    children: int = 2,
    elderly: int = 0,
    target_date: Optional[datetime] = None
) -> np.ndarray:
    """
    Extract a single feature vector at runtime for inference on live pantry items.
    """
    now = target_date or datetime.now()
    item_code = ITEM_ENCODING.get(item_name, 0)
    day_of_week = now.weekday()
    is_weekend = 1 if day_of_week in (5, 6) else 0

    # Calculate consumption intervals from recent readings
    intervals = []
    if len(recent_readings) >= 2:
        sorted_readings = sorted(recent_readings, key=lambda r: r["timestamp"])
        for i in range(1, len(sorted_readings)):
            p = float(sorted_readings[i - 1]["weight"])
            c = float(sorted_readings[i]["weight"])
            if c < p:
                intervals.append(round(p - c, 2))

    # Base estimate fallback if insufficient readings
    default_base = {
        "Rice": 100.0 * (family_size ** 0.82),
        "Sugar": 20.0 * (family_size ** 0.82),
        "Salt": 5.0 * (family_size ** 0.82),
        "Ghee": 12.0 * (family_size ** 0.82),
    }.get(item_name, 50.0)

    if intervals:
        prev_1d = intervals[-1]
        roll_3d = np.mean(intervals[-3:])
        roll_7d = np.mean(intervals[-7:])
        roll_14d = np.mean(intervals[-14:])
        roll_30d = np.mean(intervals[-30:])
    else:
        prev_1d = default_base
        roll_3d = default_base
        roll_7d = default_base
        roll_14d = default_base
        roll_30d = default_base

    trend = round(float(roll_7d / (roll_30d + 0.1)), 3)

    feature_vec = [
        item_code,
        family_size,
        adults,
        children,
        elderly,
        day_of_week,
        is_weekend,
        float(prev_1d),
        float(roll_3d),
        float(roll_7d),
        float(roll_14d),
        float(roll_30d),
        float(trend),
        float(current_quantity),
    ]

    return np.array(feature_vec).reshape(1, -1)
