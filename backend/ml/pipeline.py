"""
End-to-end Machine Learning training, chronological validation, and benchmark evaluation pipeline.
Guarantees zero future-leakage by splitting strictly on the chronological calendar date axis.
"""

import sys
from pathlib import Path

# Add project root to sys.path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    mean_absolute_error, root_mean_squared_error, r2_score,
    accuracy_score, precision_recall_fscore_support, confusion_matrix
)

from backend.ml.feature_engineering import build_time_series_features, FEATURE_COLUMNS
from backend.ml.models import (
    BaselineMovingAverage, BaselineExponentialAverage,
    build_random_forest_regressor, build_hist_gradient_boosting_regressor,
    AnomalyDetector, build_dietary_pattern_classifier
)

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_and_evaluate_pipeline(
    consumption_csv_path: Optional[Path] = None,
    household_csv_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Train and evaluate the ML pipeline on synthetic data using a strict 70/15/15 chronological split.
    Saves model artifacts and evaluation metrics report.
    """
    base_data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic"
    c_path = consumption_csv_path or (base_data_dir / "consumption_dataset.csv")
    h_path = household_csv_path or (base_data_dir / "household_dataset.csv")
    save_dir = output_dir or MODELS_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    if not c_path.exists():
        raise FileNotFoundError(f"Consumption dataset not found at {c_path}. Run generator first.")

    print(f"Loading datasets from {c_path}...")
    df_consumption = pd.read_csv(c_path)
    df_households = pd.read_csv(h_path) if h_path.exists() else None

    # 1. Feature Engineering
    print("Building strict chronological lag features...")
    df_features = build_time_series_features(df_consumption, df_households)

    # 2. Strict Chronological Split (70% Train, 15% Val, 15% Test)
    unique_dates = sorted(df_features["date"].unique())
    total_dates = len(unique_dates)
    train_cutoff_idx = int(total_dates * 0.70)
    val_cutoff_idx = int(total_dates * 0.85)

    train_dates = set(unique_dates[:train_cutoff_idx])
    val_dates = set(unique_dates[train_cutoff_idx:val_cutoff_idx])
    test_dates = set(unique_dates[val_cutoff_idx:])

    train_mask = df_features["date"].isin(train_dates)
    val_mask = df_features["date"].isin(val_dates)
    test_mask = df_features["date"].isin(test_dates)

    X_train = df_features.loc[train_mask, FEATURE_COLUMNS].values
    y_train = df_features.loc[train_mask, "consumption_grams"].values

    X_val = df_features.loc[val_mask, FEATURE_COLUMNS].values
    y_val = df_features.loc[val_mask, "consumption_grams"].values

    X_test = df_features.loc[test_mask, FEATURE_COLUMNS].values
    y_test = df_features.loc[test_mask, "consumption_grams"].values

    print(f"Dataset split: Train={len(y_train)}, Val={len(y_val)}, Test={len(y_test)}")

    # 3. Benchmark Models
    benchmarks = []

    # Model 1: Baseline 7-day Moving Average
    sma_model = BaselineMovingAverage(rolling_7d_col_idx=FEATURE_COLUMNS.index("rolling_7d_avg"))
    sma_preds = sma_model.predict(X_test)
    benchmarks.append({
        "model_name": "Baseline-7d-SMA",
        "mae": round(float(mean_absolute_error(y_test, sma_preds)), 2),
        "rmse": round(float(root_mean_squared_error(y_test, sma_preds)), 2),
        "r2": round(float(r2_score(y_test, sma_preds)), 3),
        "is_baseline": True,
    })

    # Model 2: Baseline 14-day Exponential Moving Average
    ema_model = BaselineExponentialAverage(
        prev_1d_idx=FEATURE_COLUMNS.index("prev_1d_consumption"),
        rolling_7d_idx=FEATURE_COLUMNS.index("rolling_7d_avg")
    )
    ema_preds = ema_model.predict(X_test)
    benchmarks.append({
        "model_name": "Baseline-EMA (alpha=0.2)",
        "mae": round(float(mean_absolute_error(y_test, ema_preds)), 2),
        "rmse": round(float(root_mean_squared_error(y_test, ema_preds)), 2),
        "r2": round(float(r2_score(y_test, ema_preds)), 3),
        "is_baseline": True,
    })

    # Model 3: Random Forest Regressor
    print("Training RandomForestRegressor...")
    # Subsample training data if very large for fast training
    subsample_size = min(len(y_train), 50000)
    indices = np.random.RandomState(42).choice(len(y_train), subsample_size, replace=False)
    rf_model = build_random_forest_regressor()
    rf_model.fit(X_train[indices], y_train[indices])

    rf_test_preds = np.clip(rf_model.predict(X_test), 0.0, None)
    residuals = y_test - rf_test_preds
    residual_std = float(np.std(residuals))

    benchmarks.append({
        "model_name": "RandomForestRegressor",
        "mae": round(float(mean_absolute_error(y_test, rf_test_preds)), 2),
        "rmse": round(float(root_mean_squared_error(y_test, rf_test_preds)), 2),
        "r2": round(float(r2_score(y_test, rf_test_preds)), 3),
        "is_baseline": False,
        "residual_std": round(residual_std, 2)
    })

    # Model 4: HistGradientBoostingRegressor
    print("Training HistGradientBoostingRegressor...")
    hgb_model = build_hist_gradient_boosting_regressor()
    hgb_model.fit(X_train[indices], y_train[indices])
    hgb_test_preds = np.clip(hgb_model.predict(X_test), 0.0, None)

    benchmarks.append({
        "model_name": "HistGradientBoostingRegressor",
        "mae": round(float(mean_absolute_error(y_test, hgb_test_preds)), 2),
        "rmse": round(float(root_mean_squared_error(y_test, hgb_test_preds)), 2),
        "r2": round(float(r2_score(y_test, hgb_test_preds)), 3),
        "is_baseline": False,
    })

    # Feature Importance from Random Forest
    importances = rf_model.feature_importances_
    feat_imp = {
        col: round(float(imp), 4)
        for col, imp in zip(FEATURE_COLUMNS, importances)
    }

    # 4. Anomaly Detector
    print("Fitting AnomalyDetector...")
    anomaly_detector = AnomalyDetector()
    anomaly_detector.fit(y_train[indices])

    # 5. Dietary Pattern Classifier Training
    print("Training Dietary Pattern Classifier...")
    # Build household-level synthetic feature matrix
    pattern_classes = ["NORMAL", "HIGH_SUGAR", "HIGH_SODIUM", "HIGH_FAT", "INCREASING_CONSUMPTION", "IRREGULAR"]
    class_map = {c: idx for idx, c in enumerate(pattern_classes)}

    # Generate synthetic training examples for the 6 valid behavioral patterns
    np.random.seed(42)
    clf_X = []
    clf_y = []
    for _ in range(3000):
        c_choice = np.random.choice(pattern_classes, p=[0.45, 0.15, 0.15, 0.10, 0.08, 0.07])
        if c_choice == "NORMAL":
            sugar = np.random.uniform(10, 45)
            sodium = np.random.uniform(500, 1800)
            fat = np.random.uniform(15, 55)
            trend = np.random.uniform(0.9, 1.15)
            cv = np.random.uniform(0.1, 0.5)
        elif c_choice == "HIGH_SUGAR":
            sugar = np.random.uniform(55, 120)
            sodium = np.random.uniform(500, 1800)
            fat = np.random.uniform(15, 50)
            trend = np.random.uniform(0.9, 1.2)
            cv = np.random.uniform(0.2, 0.6)
        elif c_choice == "HIGH_SODIUM":
            sugar = np.random.uniform(15, 45)
            sodium = np.random.uniform(2100, 4500)
            fat = np.random.uniform(15, 50)
            trend = np.random.uniform(0.9, 1.2)
            cv = np.random.uniform(0.2, 0.6)
        elif c_choice == "HIGH_FAT":
            sugar = np.random.uniform(15, 45)
            sodium = np.random.uniform(500, 1800)
            fat = np.random.uniform(65, 120)
            trend = np.random.uniform(0.9, 1.2)
            cv = np.random.uniform(0.2, 0.6)
        elif c_choice == "INCREASING_CONSUMPTION":
            sugar = np.random.uniform(20, 45)
            sodium = np.random.uniform(800, 1800)
            fat = np.random.uniform(20, 50)
            trend = np.random.uniform(1.35, 1.8)
            cv = np.random.uniform(0.2, 0.6)
        else:  # IRREGULAR
            sugar = np.random.uniform(20, 45)
            sodium = np.random.uniform(800, 1800)
            fat = np.random.uniform(20, 50)
            trend = np.random.uniform(0.9, 1.2)
            cv = np.random.uniform(0.90, 1.4)

        clf_X.append([sugar, sodium, fat, trend, cv])
        clf_y.append(class_map[c_choice])

    clf_X = np.array(clf_X)
    clf_y = np.array(clf_y)

    c_train_idx = int(len(clf_X) * 0.8)
    diet_clf = build_dietary_pattern_classifier()
    diet_clf.fit(clf_X[:c_train_idx], clf_y[:c_train_idx])

    clf_test_preds = diet_clf.predict(clf_X[c_train_idx:])
    acc = float(accuracy_score(clf_y[c_train_idx:], clf_test_preds))
    prec, rec, f1, _ = precision_recall_fscore_support(clf_y[c_train_idx:], clf_test_preds, average="macro")
    cm = confusion_matrix(clf_y[c_train_idx:], clf_test_preds).tolist()

    classification_metrics = {
        "accuracy": round(acc, 3),
        "macro_precision": round(float(prec), 3),
        "macro_recall": round(float(rec), 3),
        "macro_f1": round(float(f1), 3),
        "classes": pattern_classes,
        "confusion_matrix": cm,
    }

    # 6. Save Model Artifacts
    print(f"Saving model artifacts to {save_dir}...")
    joblib.dump({
        "model": rf_model,
        "residual_std": residual_std,
        "feature_columns": FEATURE_COLUMNS,
    }, save_dir / "consumption_model.joblib")

    joblib.dump({
        "classifier": diet_clf,
        "classes": pattern_classes,
        "class_map": class_map,
    }, save_dir / "dietary_classifier.joblib")

    joblib.dump(anomaly_detector, save_dir / "anomaly_detector.joblib")

    # 7. Save Evaluation Metrics JSON
    report = {
        "notice": (
            "This evaluation is performed on synthetically generated multi-household pantry data "
            "using a strict chronological 70/15/15 train/val/test split to prevent time-series leakage. "
            "It must not be represented as real human household measurements."
        ),
        "dataset_size_records": len(df_features),
        "households_count": int(df_consumption["household_id"].nunique()),
        "train_size": len(y_train),
        "val_size": len(y_val),
        "test_size": len(y_test),
        "regression_benchmarks": benchmarks,
        "classification_metrics": classification_metrics,
        "feature_importance": feat_imp,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(save_dir / "model_metrics.json", "w") as f:
        json.dump(report, f, indent=2)

    print("Pipeline training and evaluation completed successfully.")
    return report


if __name__ == "__main__":
    train_and_evaluate_pipeline()
