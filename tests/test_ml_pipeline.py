import pytest
import numpy as np
from backend.ml.models import (
    BaselineMovingAverage, BaselineExponentialAverage,
    AnomalyDetector
)
from backend.ml.predictor import PantryPredictor
from backend import models


def test_baseline_moving_average_non_negative():
    """Verify that moving average baseline predictions are non-negative and match column."""
    sma = BaselineMovingAverage(rolling_7d_col_idx=1)
    X = np.array([
        [10.0, 150.0],
        [20.0, 0.0],
        [30.0, -5.0],
    ])
    preds = sma.predict(X)
    assert preds[0] == 150.0
    assert preds[1] == 0.0
    assert preds[2] == 0.0  # Clipped at 0.0


def test_anomaly_detector_scoring():
    """AnomalyDetector flags genuine spikes (> 2.5 sigma) and ignores normal variation."""
    detector = AnomalyDetector()
    # Baseline mean 100g, std 15g
    rolling_mean = 100.0
    rolling_std = 15.0

    # 1. Normal consumption (110g -> z = 0.67)
    is_anomaly, score, expl = detector.evaluate_reading(110.0, rolling_mean, rolling_std)
    assert not is_anomaly
    assert score < 2.5

    # 2. Huge spike (300g -> z = 13.3)
    is_anomaly, score, expl = detector.evaluate_reading(300.0, rolling_mean, rolling_std)
    assert is_anomaly
    assert score > 2.5
    assert "Unusual consumption" in expl
    assert "300.0g" in expl


def test_predictor_depletion_and_ranges():
    """Verify PantryPredictor outputs valid ranges, non-negative forecasts, and family scaling."""
    predictor = PantryPredictor()

    class MockItem:
        id = 1
        name = "Rice"
        unit = "g"
        current_quantity = 3000.0
        minimum_quantity = 1000.0
        high_intake_threshold = 300.0
        readings = []

    class MockHouseholdSmall:
        family_size = 2
        adults_count = 2
        children_count = 0
        elderly_count = 0

    class MockHouseholdLarge:
        family_size = 6
        adults_count = 3
        children_count = 2
        elderly_count = 1

    pred_small = predictor.predict_item_consumption(MockItem(), MockHouseholdSmall())
    pred_large = predictor.predict_item_consumption(MockItem(), MockHouseholdLarge())

    # 1. Non-negative predictions
    assert pred_small["predicted_daily_consumption"] > 0.0
    assert pred_large["predicted_daily_consumption"] > 0.0

    # 2. Family size scaling (family of 6 consumes more than family of 2)
    assert pred_large["predicted_daily_consumption"] > pred_small["predicted_daily_consumption"]

    # 3. 90% prediction range ordering: low <= predicted <= high
    assert pred_small["prediction_range_90_low"] <= pred_small["predicted_daily_consumption"]
    assert pred_small["predicted_daily_consumption"] <= pred_small["prediction_range_90_high"]

    # 4. Remaining days & Depletion date
    assert pred_small["remaining_days_ml"] is not None
    assert pred_small["predicted_depletion_date"] is not None
