"""
Lightweight Machine Learning models and baseline benchmarks for pantry consumption forecasting,
anomaly detection, and dietary pattern classification.
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor, RandomForestClassifier, IsolationForest
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score, accuracy_score, precision_recall_fscore_support, confusion_matrix


class BaselineMovingAverage(BaseEstimator, RegressorMixin):
    """
    Transparent 7-day Simple Moving Average baseline regressor.
    Predicts based strictly on historical rolling 7-day average.
    """
    def __init__(self, rolling_7d_col_idx: int = 9):
        self.rolling_7d_col_idx = rolling_7d_col_idx

    def fit(self, X, y=None):
        # Baseline requires no parameter fitting
        return self

    def predict(self, X):
        X_arr = np.asarray(X)
        preds = X_arr[:, self.rolling_7d_col_idx]
        return np.clip(preds, 0.0, None)


class BaselineExponentialAverage(BaseEstimator, RegressorMixin):
    """
    Exponential Moving Average baseline (alpha=0.2).
    0.2 * prev_day + 0.8 * rolling_7d.
    """
    def __init__(self, prev_1d_idx: int = 7, rolling_7d_idx: int = 9, alpha: float = 0.2):
        self.prev_1d_idx = prev_1d_idx
        self.rolling_7d_idx = rolling_7d_idx
        self.alpha = alpha

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        X_arr = np.asarray(X)
        p1 = X_arr[:, self.prev_1d_idx]
        r7 = X_arr[:, self.rolling_7d_idx]
        preds = self.alpha * p1 + (1.0 - self.alpha) * r7
        return np.clip(preds, 0.0, None)


def build_random_forest_regressor() -> RandomForestRegressor:
    """Instantiate interpretable Random Forest regressor with depth bounds."""
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )


def build_hist_gradient_boosting_regressor() -> HistGradientBoostingRegressor:
    """Instantiate lightweight HistGradientBoosting regressor."""
    return HistGradientBoostingRegressor(
        max_iter=100,
        max_depth=6,
        min_samples_leaf=10,
        random_state=42
    )


class AnomalyDetector:
    """
    Consumption anomaly detector combining Isolation Forest and rolling Z-score.
    Avoids medical claims; uses terminology 'Unusual consumption event'.
    """
    def __init__(self, contamination: float = 0.03):
        self.iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        self.is_fitted = False

    def fit(self, consumption_values: np.ndarray):
        vals = np.asarray(consumption_values).reshape(-1, 1)
        self.iso_forest.fit(vals)
        self.is_fitted = True
        return self

    def evaluate_reading(
        self,
        consumed_grams: float,
        rolling_mean: float,
        rolling_std: float
    ) -> Tuple[bool, float, str]:
        """
        Evaluate if consumed_grams is an unusual consumption spike.
        Returns (is_anomaly, deviation_score, context_explanation).
        """
        if consumed_grams <= 0:
            return False, 0.0, "Zero consumption (no usage)"

        # Safe std check
        safe_std = max(rolling_std, 5.0)
        z_score = (consumed_grams - rolling_mean) / safe_std

        # Check if deviation exceeds 2.5 sigma
        is_z_anomaly = z_score > 2.5

        # Check IsolationForest if fitted
        is_if_anomaly = False
        if self.is_fitted:
            pred = self.iso_forest.predict([[consumed_grams]])[0]
            is_if_anomaly = (pred == -1)

        is_anomaly = is_z_anomaly or (is_if_anomaly and consumed_grams > rolling_mean * 1.5)

        if is_anomaly:
            pct_diff = round(((consumed_grams - rolling_mean) / max(rolling_mean, 1.0)) * 100, 1)
            explanation = (
                f"Unusual consumption: Consumed {consumed_grams}g vs "
                f"expected ~{round(rolling_mean, 1)}g (+{pct_diff}% / +{round(z_score, 1)}σ)"
            )
        else:
            explanation = "Consumption within normal expected variance"

        return is_anomaly, round(float(z_score), 2), explanation


def build_dietary_pattern_classifier() -> RandomForestClassifier:
    """Instantiate multi-class classifier for dietary patterns."""
    return RandomForestClassifier(
        n_estimators=80,
        max_depth=6,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
