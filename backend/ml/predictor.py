"""
Runtime prediction and stock depletion forecasting engine.
Combines current container weight with ML model inferences to project consumption,
calendar depletion dates, and 90% empirical prediction ranges.
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import joblib
from sqlalchemy.orm import Session

from backend.models import Item, HouseholdProfile, WeightReading
from backend.ml.feature_engineering import extract_live_features_for_item
from backend.calculations import calculate_remaining_days, calculate_average_daily_intake

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "models"


class PantryPredictor:
    """Predictor service for pantry consumption forecasting and stock depletion."""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or MODELS_DIR
        self._model_data = None
        self._anomaly_detector = None
        self._dietary_classifier = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Load trained models from disk if available."""
        model_path = self.models_dir / "consumption_model.joblib"
        if model_path.exists():
            try:
                self._model_data = joblib.load(model_path)
            except Exception:
                self._model_data = None

        anomaly_path = self.models_dir / "anomaly_detector.joblib"
        if anomaly_path.exists():
            try:
                self._anomaly_detector = joblib.load(anomaly_path)
            except Exception:
                self._anomaly_detector = None

        diet_path = self.models_dir / "dietary_classifier.joblib"
        if diet_path.exists():
            try:
                self._dietary_classifier = joblib.load(diet_path)
            except Exception:
                self._dietary_classifier = None

    def predict_item_consumption(
        self,
        item: Item,
        household: HouseholdProfile
    ) -> Dict[str, Any]:
        """
        Predict future consumption and stock depletion trajectory for an item.
        """
        readings_data = [
            {"id": r.id, "weight": r.weight, "timestamp": r.timestamp}
            for r in item.readings
        ]
        avg_math_daily, days_with_data = calculate_average_daily_intake(readings_data)
        rem_days_math = calculate_remaining_days(item.current_quantity, avg_math_daily)

        # Baseline per-person rates if model not yet fitted
        base_rate = {
            "Rice": 100.0,
            "Sugar": 20.0,
            "Salt": 5.0,
            "Ghee": 12.0,
        }.get(item.name, 50.0)

        family_size = getattr(household, "family_size", 4)
        adults = getattr(household, "adults_count", 2)
        children = getattr(household, "children_count", 2)
        elderly = getattr(household, "elderly_count", 0)

        # Default fallback estimate (economies of scale)
        fallback_daily = base_rate * (family_size ** 0.82)

        predicted_daily = fallback_daily
        model_name = "Baseline Moving Average"
        residual_std = 15.0

        if self._model_data and "model" in self._model_data:
            try:
                feature_vec = extract_live_features_for_item(
                    item_name=item.name,
                    current_quantity=item.current_quantity,
                    recent_readings=readings_data,
                    family_size=family_size,
                    adults=adults,
                    children=children,
                    elderly=elderly
                )
                pred_val = float(self._model_data["model"].predict(feature_vec)[0])
                predicted_daily = max(0.0, pred_val)
                model_name = "RandomForestRegressor"
                residual_std = float(self._model_data.get("residual_std", 15.0))
            except Exception:
                predicted_daily = fallback_daily
                model_name = "Baseline Moving Average (Fallback)"

        predicted_daily = round(predicted_daily, 1)

        # Multi-day projections
        pred_7d = round(predicted_daily * 7.0, 1)
        pred_14d = round(predicted_daily * 14.0, 1)
        pred_30d = round(predicted_daily * 30.0, 1)

        # ML Depletion calculation
        if item.current_quantity > 0 and predicted_daily > 0:
            rem_days_ml = round(item.current_quantity / predicted_daily, 1)
            depletion_date = (datetime.now() + timedelta(days=rem_days_ml)).strftime("%Y-%m-%d")
        else:
            rem_days_ml = None
            depletion_date = None

        # 90% Empirical Prediction Range (Residual-based)
        margin = 1.645 * residual_std
        range_low = round(max(0.0, predicted_daily - margin), 1)
        range_high = round(predicted_daily + margin, 1)

        # Availability status
        if item.current_quantity <= 0:
            stock_status = "UNAVAILABLE"
        elif item.current_quantity <= item.minimum_quantity:
            stock_status = "LOW"
        else:
            stock_status = "AVAILABLE"

        return {
            "item_id": item.id,
            "item_name": item.name,
            "unit": item.unit,
            "current_quantity": item.current_quantity,
            "historical_average_daily": avg_math_daily,
            "predicted_daily_consumption": predicted_daily,
            "predicted_7d_consumption": pred_7d,
            "predicted_14d_consumption": pred_14d,
            "predicted_30d_consumption": pred_30d,
            "remaining_days_math": rem_days_math,
            "remaining_days_ml": rem_days_ml,
            "predicted_depletion_date": depletion_date,
            "prediction_range_90_low": range_low,
            "prediction_range_90_high": range_high,
            "model_used": model_name,
            "stock_status": stock_status,
        }

    def predict_all_items(
        self,
        items: List[Item],
        household: HouseholdProfile
    ) -> List[Dict[str, Any]]:
        """Predict consumption and depletion for all given items."""
        return [self.predict_item_consumption(item, household) for item in items]


# Singleton instance
_predictor_instance = None


def get_predictor() -> PantryPredictor:
    """Retrieve or initialize the global PantryPredictor instance."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = PantryPredictor()
    return _predictor_instance
