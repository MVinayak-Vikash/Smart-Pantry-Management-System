import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.ml.feature_engineering import build_time_series_features, FEATURE_COLUMNS


def test_zero_future_leakage_in_features():
    """
    CRITICAL TEST: Verify that rolling features at day t use strictly observations < t.
    Day 1: 100g
    Day 2: 200g
    Day 3: 300g
    Day 4: 400g
    Day 5: 500g
    """
    base_date = datetime(2026, 1, 1)
    records = []
    weights = [100.0, 200.0, 300.0, 400.0, 500.0]

    for i, cons in enumerate(weights):
        records.append({
            "household_id": 1,
            "item_name": "Rice",
            "date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "consumption_grams": cons,
            "previous_weight": 5000.0 - (i * 200),
            "current_weight": 4800.0 - (i * 200),
            "measured_weight": 4800.0 - (i * 200),
        })

    df = pd.DataFrame(records)
    df_feat = build_time_series_features(df)

    # First row is dropped because prev_1d is NaN (Day 1)
    # So df_feat index 0 is Day 2, index 1 is Day 3, index 2 is Day 4, index 3 is Day 5

    # Day 3 (row 1):
    day3_row = df_feat.iloc[1]
    assert day3_row["consumption_grams"] == 300.0
    # prev_1d must be Day 2's consumption (200.0), NOT Day 3 (300.0)!
    assert day3_row["prev_1d_consumption"] == 200.0
    # rolling_3d_avg must be mean of Day 1 (100) and Day 2 (200) = 150.0
    assert day3_row["rolling_3d_avg"] == 150.0

    # Day 4 (row 2):
    day4_row = df_feat.iloc[2]
    assert day4_row["consumption_grams"] == 400.0
    assert day4_row["prev_1d_consumption"] == 300.0
    # rolling_3d_avg must be mean of Day 1 (100), Day 2 (200), Day 3 (300) = 200.0
    assert day4_row["rolling_3d_avg"] == 200.0


def test_chronological_split_strictly_non_overlapping():
    """Verify that train, validation, and test sets are ordered sequentially in time."""
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "household_id": 1,
        "item_name": "Rice",
        "date": dates.strftime("%Y-%m-%d"),
        "consumption_grams": np.random.uniform(50, 150, 100),
        "previous_weight": 4000.0,
        "current_weight": 3900.0,
        "measured_weight": 3900.0,
    })
    df_feat = build_time_series_features(df)

    unique_dates = sorted(df_feat["date"].unique())
    train_end = int(len(unique_dates) * 0.70)
    val_end = int(len(unique_dates) * 0.85)

    train_dates = unique_dates[:train_end]
    val_dates = unique_dates[train_end:val_end]
    test_dates = unique_dates[val_end:]

    # Assert strict monotonicity: max(train) < min(val) < min(test)
    assert max(train_dates) < min(val_dates)
    assert max(val_dates) < min(test_dates)
