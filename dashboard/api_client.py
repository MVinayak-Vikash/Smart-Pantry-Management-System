"""
Resilient API Client for Smart Pantry Management System.
Connects via HTTP to FastAPI backend with automatic, transparent fallback
to direct SQLite access so the Streamlit dashboard always works seamlessly.
"""

import os
import requests
from typing import Dict, Any, List, Optional, Tuple

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT_SEC = 2.5


class PantryClient:
    """Client providing unified access to pantry data via REST or direct DB."""

    @staticmethod
    def is_api_online() -> bool:
        """Check if FastAPI backend is reachable."""
        try:
            r = requests.get(f"{API_BASE_URL}/health", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

    @classmethod
    def get_dashboard_summary(cls) -> Tuple[Optional[Dict[str, Any]], str]:
        """Fetch dashboard summary metrics."""
        try:
            r = requests.get(f"{API_BASE_URL}/dashboard", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json(), "API"
        except Exception:
            pass

        # Fallback to direct DB
        try:
            from backend.database import SessionLocal, init_db
            from backend import crud, schemas
            init_db()
            db = SessionLocal()
            try:
                items = crud.get_items(db)
                items_summary = []
                avail = low = unavail = high = 0
                for item in items:
                    m = crud.compute_item_metrics(item)
                    summary = schemas.ItemSummaryResponse(**m)
                    items_summary.append(summary.model_dump())
                    if summary.availability_status == "AVAILABLE":
                        avail += 1
                    elif summary.availability_status == "LOW":
                        low += 1
                    else:
                        unavail += 1
                    if summary.intake_status == "HIGH":
                        high += 1
                return {
                    "items": items_summary,
                    "total_items": len(items_summary),
                    "available_count": avail,
                    "low_count": low,
                    "unavailable_count": unavail,
                    "high_intake_count": high,
                }, "DirectDB"
            finally:
                db.close()
        except Exception as e:
            return None, str(e)

    @classmethod
    def get_household(cls) -> Tuple[Optional[Dict[str, Any]], str]:
        """Retrieve active household profile."""
        try:
            r = requests.get(f"{API_BASE_URL}/household", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json(), "API"
        except Exception:
            pass

        try:
            from backend.database import SessionLocal, init_db
            from backend import crud, schemas
            init_db()
            db = SessionLocal()
            try:
                p = crud.get_household_profile(db, 1)
                return schemas.HouseholdProfileResponse.model_validate(p).model_dump(), "DirectDB"
            finally:
                db.close()
        except Exception as e:
            return None, str(e)

    @classmethod
    def update_household(cls, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update household profile attributes."""
        try:
            r = requests.put(f"{API_BASE_URL}/household", json=data, timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return True, "Household updated via FastAPI."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud
            db = SessionLocal()
            try:
                crud.update_household_profile(db, data, 1)
                return True, "Household updated directly in database."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)

    @classmethod
    def get_items(cls) -> List[Dict[str, Any]]:
        """Retrieve all pantry items."""
        try:
            r = requests.get(f"{API_BASE_URL}/items", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud, schemas
            db = SessionLocal()
            try:
                items = crud.get_items(db)
                return [schemas.ItemSummaryResponse(**crud.compute_item_metrics(i)).model_dump() for i in items]
            finally:
                db.close()
        except Exception:
            return []

    @classmethod
    def get_item_detail(cls, item_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve detailed profile and history for an item."""
        try:
            r = requests.get(f"{API_BASE_URL}/items/{item_id}", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud, schemas
            db = SessionLocal()
            try:
                item = crud.get_item_by_id(db, item_id)
                if not item:
                    return None
                m = crud.compute_item_metrics(item)
                readings = [schemas.WeightReadingResponse.model_validate(r).model_dump() for r in item.readings]
                m["recent_weight_history"] = readings
                return m
            finally:
                db.close()
        except Exception:
            return None

    @classmethod
    def get_item_consumption(cls, item_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve consumption intervals and metrics for an item."""
        try:
            r = requests.get(f"{API_BASE_URL}/items/{item_id}/consumption", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud
            db = SessionLocal()
            try:
                return crud.get_item_consumption_history(db, item_id)
            finally:
                db.close()
        except Exception:
            return None

    @classmethod
    def get_predictions(cls) -> List[Dict[str, Any]]:
        """Retrieve ML forecasts and depletion countdowns for all items."""
        try:
            r = requests.get(f"{API_BASE_URL}/predictions", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud
            from backend.ml.predictor import get_predictor
            db = SessionLocal()
            try:
                household = crud.get_household_profile(db, 1)
                items = crud.get_items(db)
                predictor = get_predictor()
                return predictor.predict_all_items(items, household)
            finally:
                db.close()
        except Exception:
            return []

    @classmethod
    def get_diet_summary(cls, period: str = "today") -> Optional[Dict[str, Any]]:
        """Retrieve nutrition summary and dietary pattern."""
        try:
            r = requests.get(f"{API_BASE_URL}/diet/summary?period={period}", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud, calculations
            db = SessionLocal()
            try:
                items = crud.get_items(db)
                items_map = {i.id: i for i in items}
                items_history = [crud.get_item_consumption_history(db, i.id) for i in items]
                daily = calculations.aggregate_pantry_nutrition_by_day(items_history, items_map)
                meals = crud.get_meal_logs(db, 1)

                pantry_tot = {"calories_kcal": 0.0, "carbohydrates_g": 0.0, "protein_g": 0.0, "fat_g": 0.0, "sugar_g": 0.0, "sodium_mg": 0.0, "fiber_g": 0.0}
                for d in daily.values():
                    for k in pantry_tot:
                        pantry_tot[k] = round(pantry_tot[k] + d.get(k, 0.0), 1)

                comb = calculations.combine_pantry_and_manual_nutrition(pantry_tot, meals)
                pattern, desc = calculations.classify_dietary_pattern(
                    sugar_avg_daily=pantry_tot["sugar_g"] / max(1, len(daily)),
                    sodium_avg_daily=pantry_tot["sodium_mg"] / max(1, len(daily)),
                    fat_avg_daily=pantry_tot["fat_g"] / max(1, len(daily)),
                    days_with_data=len(daily)
                )

                return {
                    "disclaimer": "Estimated intake from tracked pantry foods and logged meals — for lifestyle awareness, not medical advice",
                    "period": period,
                    "days_analyzed": len(daily),
                    "tracked_pantry_intake": comb["tracked_pantry"],
                    "manual_logged_intake": comb["manual_logged"],
                    "total_combined_intake": comb["total_combined"],
                    "dietary_pattern": pattern,
                    "dietary_pattern_description": desc,
                    "per_item_calories": {},
                }
            finally:
                db.close()
        except Exception:
            return None

    @classmethod
    def get_diet_trends(cls) -> List[Dict[str, Any]]:
        """Retrieve daily nutrition time-series."""
        try:
            r = requests.get(f"{API_BASE_URL}/diet/trends", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud, calculations
            db = SessionLocal()
            try:
                items = crud.get_items(db)
                items_map = {i.id: i for i in items}
                items_history = [crud.get_item_consumption_history(db, i.id) for i in items]
                daily = calculations.aggregate_pantry_nutrition_by_day(items_history, items_map)
                trends = []
                for d_str in sorted(daily.keys()):
                    val = daily[d_str]
                    trends.append({
                        "date": d_str,
                        "calories": val["calories_kcal"],
                        "carbohydrates": val["carbohydrates_g"],
                        "protein": val["protein_g"],
                        "fat": val["fat_g"],
                        "sugar": val["sugar_g"],
                        "sodium": val["sodium_mg"],
                        "source": "tracked_pantry"
                    })
                return trends
            finally:
                db.close()
        except Exception:
            return []

    @classmethod
    def log_meal(cls, meal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Log manual external meal."""
        try:
            r = requests.post(f"{API_BASE_URL}/meals", json=meal_data, timeout=TIMEOUT_SEC)
            if r.status_code == 201:
                return True, "Meal logged successfully via API."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud
            db = SessionLocal()
            try:
                crud.create_meal_log(db, meal_data, 1)
                return True, "Meal logged directly into database."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)

    @classmethod
    def get_meal_logs(cls) -> List[Dict[str, Any]]:
        """List recent manual meal logs."""
        try:
            r = requests.get(f"{API_BASE_URL}/meals", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud, schemas
            db = SessionLocal()
            try:
                meals = crud.get_meal_logs(db, 1)
                return [schemas.MealLogResponse.model_validate(m).model_dump() for m in meals]
            finally:
                db.close()
        except Exception:
            return []

    @classmethod
    def get_recipe_recommendations(cls) -> Optional[Dict[str, Any]]:
        """Retrieve categorized recipe recommendations."""
        try:
            r = requests.get(f"{API_BASE_URL}/recipes/recommendations", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend.recipes.engine import evaluate_recipe_recommendations
            db = SessionLocal()
            try:
                return evaluate_recipe_recommendations(db, 1)
            finally:
                db.close()
        except Exception:
            return None

    @classmethod
    def get_shopping_list(cls) -> List[Dict[str, Any]]:
        """Retrieve shopping items list."""
        try:
            r = requests.get(f"{API_BASE_URL}/shopping-list", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud, schemas
            db = SessionLocal()
            try:
                items = crud.get_shopping_items(db, 1)
                return [schemas.ShoppingItemResponse.model_validate(i).model_dump() for i in items]
            finally:
                db.close()
        except Exception:
            return []

    @classmethod
    def generate_shopping_list(cls) -> Tuple[bool, str]:
        """Trigger shopping list generation."""
        try:
            r = requests.post(f"{API_BASE_URL}/shopping-list/generate", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return True, "Shopping list generated via API."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend.shopping.generator import generate_restock_recommendations
            db = SessionLocal()
            try:
                generate_restock_recommendations(db, 1)
                return True, "Shopping list evaluated directly."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)

    @classmethod
    def mark_shopping_purchased(cls, item_id: int) -> Tuple[bool, str]:
        """Mark shopping item as purchased."""
        try:
            r = requests.post(f"{API_BASE_URL}/shopping-list/{item_id}/purchase", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return True, "Marked as purchased via API."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud
            db = SessionLocal()
            try:
                crud.mark_shopping_item_purchased(db, item_id, record_refill=True)
                return True, "Marked as purchased directly."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)

    @classmethod
    def get_alerts(cls, unresolved_only: bool = False) -> List[Dict[str, Any]]:
        """Retrieve system alerts."""
        try:
            r = requests.get(f"{API_BASE_URL}/alerts?unresolved_only={unresolved_only}", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend.alerts.engine import evaluate_and_sync_alerts
            from backend import crud, schemas
            db = SessionLocal()
            try:
                evaluate_and_sync_alerts(db, 1)
                alerts = crud.get_alerts(db, 1, unresolved_only=unresolved_only)
                return [schemas.AlertLogResponse.model_validate(a).model_dump() for a in alerts]
            finally:
                db.close()
        except Exception:
            return []

    @classmethod
    def resolve_alert(cls, alert_id: int) -> Tuple[bool, str]:
        """Resolve an alert."""
        try:
            r = requests.post(f"{API_BASE_URL}/alerts/{alert_id}/resolve", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return True, "Alert resolved via API."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud
            db = SessionLocal()
            try:
                crud.resolve_alert(db, alert_id)
                return True, "Alert resolved directly."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)

    @classmethod
    def get_ml_evaluation(cls) -> Optional[Dict[str, Any]]:
        """Retrieve ML model evaluation report."""
        try:
            r = requests.get(f"{API_BASE_URL}/ml/evaluation", timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

        try:
            import json
            from pathlib import Path
            metrics_path = Path(__file__).resolve().parent.parent / "data" / "models" / "model_metrics.json"
            if metrics_path.exists():
                with open(metrics_path, "r") as f:
                    return json.load(f)
        except Exception:
            return None

    @classmethod
    def post_simulated_reading(cls, item_id: int, weight: float) -> Tuple[bool, str]:
        """Submit a simulated weight reading."""
        try:
            r = requests.post(f"{API_BASE_URL}/items/{item_id}/weight", json={"weight": weight}, timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                return True, "Telemetry reading recorded via FastAPI."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend import crud
            from backend.alerts.engine import evaluate_and_sync_alerts
            db = SessionLocal()
            try:
                crud.create_weight_reading(db, item_id, weight)
                evaluate_and_sync_alerts(db)
                return True, "Telemetry reading recorded directly in SQLite."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)

    @classmethod
    def simulate_advance_days(cls, num_days: int) -> Tuple[bool, str]:
        """Advance simulation by N days."""
        try:
            r = requests.post(f"{API_BASE_URL}/simulation/simulate-days?num_days={num_days}", timeout=10.0)
            if r.status_code == 200:
                return True, f"Advanced simulation by {num_days} days via API."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend.simulation.engine import simulate_advance_days
            db = SessionLocal()
            try:
                res = simulate_advance_days(db, num_days=num_days, household_id=1)
                return True, f"Advanced {res['days_advanced']} days ({res['readings_logged']} readings logged)."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)

    @classmethod
    def reset_demo_database(cls) -> Tuple[bool, str]:
        """Reset demo database to fresh default state."""
        try:
            r = requests.post(f"{API_BASE_URL}/simulation/reset", timeout=5.0)
            if r.status_code == 200:
                return True, "Demo database reset successfully via API."
        except Exception:
            pass

        try:
            from backend.database import SessionLocal
            from backend.simulation.engine import reset_demo_environment
            db = SessionLocal()
            try:
                reset_demo_environment(db)
                return True, "Demo database reset directly in SQLite."
            finally:
                db.close()
        except Exception as e:
            return False, str(e)
