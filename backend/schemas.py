from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator


# ===================================================
# PHASE 1 PRESERVED SCHEMAS & EXTENSIONS
# ===================================================

class WeightReadingCreate(BaseModel):
    weight: float = Field(..., ge=0, description="Weight in grams, must be non-negative")
    timestamp: Optional[datetime] = None


class WeightReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    weight: float
    timestamp: datetime


class ConsumptionRecord(BaseModel):
    timestamp: datetime
    previous_weight: float
    current_weight: float
    consumption: float
    refill_amount: float


class ItemSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit: str
    current_quantity: float
    minimum_quantity: float
    availability_status: str
    average_daily_intake: Optional[float] = None
    high_intake_threshold: float
    intake_status: str
    remaining_days: Optional[float] = None

    # Extended optional fields (backward compatible defaults)
    category: Optional[str] = "General"
    calories_per_100g: Optional[float] = 0.0
    rfid_uid: Optional[str] = None
    storage_location: Optional[str] = "Pantry Shelf"
    is_perishable: Optional[bool] = False
    active: Optional[bool] = True


class ItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit: str
    initial_quantity: float
    current_quantity: float
    minimum_quantity: float
    availability_status: str
    average_daily_intake: Optional[float] = None
    high_intake_threshold: float
    intake_status: str
    remaining_days: Optional[float] = None
    rfid_uid: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    recent_weight_history: List[WeightReadingResponse] = []

    # Extended fields
    category: str = "General"
    serving_size_g: float = 50.0
    calories_per_100g: float = 0.0
    carbohydrates_per_100g: float = 0.0
    protein_per_100g: float = 0.0
    fat_per_100g: float = 0.0
    sugar_per_100g: float = 0.0
    sodium_mg_per_100g: float = 0.0
    fiber_per_100g: float = 0.0
    expiry_date: Optional[datetime] = None
    storage_location: Optional[str] = "Pantry Shelf"
    is_perishable: bool = False
    active: bool = True
    nutrition_source: str = "USDA FoodData Central / NIN India (Reference / Demo Values)"


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    unit: str = "g"
    initial_quantity: float = Field(..., ge=0)
    current_quantity: Optional[float] = None
    minimum_quantity: float = Field(..., ge=0)
    high_intake_threshold: float = Field(..., ge=0)
    category: str = "General"
    serving_size_g: float = 50.0
    calories_per_100g: float = 0.0
    carbohydrates_per_100g: float = 0.0
    protein_per_100g: float = 0.0
    fat_per_100g: float = 0.0
    sugar_per_100g: float = 0.0
    sodium_mg_per_100g: float = 0.0
    fiber_per_100g: float = 0.0
    rfid_uid: Optional[str] = None
    storage_location: Optional[str] = "Pantry Shelf"
    is_perishable: bool = False


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    minimum_quantity: Optional[float] = Field(None, ge=0)
    high_intake_threshold: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    storage_location: Optional[str] = None
    is_perishable: Optional[bool] = None
    active: Optional[bool] = None
    rfid_uid: Optional[str] = None


class ConsumptionHistoryResponse(BaseModel):
    item_id: int
    item_name: str
    unit: str
    records: List[ConsumptionRecord]
    total_consumption: float
    total_refill: float
    days_with_data: int
    average_daily_intake: Optional[float] = None


class DashboardSummaryResponse(BaseModel):
    items: List[ItemSummaryResponse]
    total_items: int
    available_count: int
    low_count: int
    unavailable_count: int
    high_intake_count: int


# ===================================================
# HOUSEHOLD PROFILE SCHEMAS
# ===================================================

class HouseholdProfileCreate(BaseModel):
    household_name: str = "My Household"
    family_size: int = Field(4, ge=1, description="Total members in household, must be >= 1")
    adults_count: int = Field(2, ge=0)
    children_count: int = Field(2, ge=0)
    elderly_count: int = Field(0, ge=0)
    activity_profile: str = Field("MODERATE", description="SEDENTARY, MODERATE, or ACTIVE")
    dietary_preference: str = Field("BALANCED", description="BALANCED, LOW_SUGAR, LOW_SODIUM, VEGETARIAN")

    @model_validator(mode="after")
    def validate_demographics_sum(self):
        total = self.adults_count + self.children_count + self.elderly_count
        if total != self.family_size:
            raise ValueError(
                f"Demographic sum (adults={self.adults_count} + children={self.children_count} + "
                f"elderly={self.elderly_count} = {total}) must equal family_size={self.family_size}"
            )
        return self


class HouseholdProfileUpdate(BaseModel):
    household_name: Optional[str] = None
    family_size: Optional[int] = Field(None, ge=1)
    adults_count: Optional[int] = Field(None, ge=0)
    children_count: Optional[int] = Field(None, ge=0)
    elderly_count: Optional[int] = Field(None, ge=0)
    activity_profile: Optional[str] = None
    dietary_preference: Optional[str] = None

    @model_validator(mode="after")
    def validate_demographics_if_provided(self):
        # If any demographic or family_size field is provided, ensure consistency
        fields_present = [self.adults_count, self.children_count, self.elderly_count, self.family_size]
        if any(f is not None for f in fields_present):
            # When all are provided, enforce exact sum
            if all(f is not None for f in fields_present):
                total = self.adults_count + self.children_count + self.elderly_count
                if total != self.family_size:
                    raise ValueError(
                        f"Demographic sum ({self.adults_count} + {self.children_count} + "
                        f"{self.elderly_count} = {total}) must equal family_size={self.family_size}"
                    )
        return self


class HouseholdProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_name: str
    family_size: int
    adults_count: int
    children_count: int
    elderly_count: int
    activity_profile: str
    dietary_preference: str
    created_at: datetime
    updated_at: datetime


# ===================================================
# HARDWARE TELEMETRY SCHEMAS
# ===================================================

class TelemetryWeightPayload(BaseModel):
    device_id: Optional[str] = "ESP32_PANTRY_01"
    rfid_uid: Optional[str] = None
    item_id: Optional[int] = None
    weight: float = Field(..., ge=0, description="Measured weight in grams")
    timestamp: Optional[datetime] = None


# ===================================================
# NUTRITION & MEAL LOGGING SCHEMAS
# ===================================================

class MealLogCreate(BaseModel):
    meal_name: str = Field(..., min_length=1)
    description: Optional[str] = None
    calories: float = Field(0.0, ge=0)
    carbohydrates: float = Field(0.0, ge=0)
    protein: float = Field(0.0, ge=0)
    fat: float = Field(0.0, ge=0)
    sugar: float = Field(0.0, ge=0)
    sodium: float = Field(0.0, ge=0)
    fiber: float = Field(0.0, ge=0)
    timestamp: Optional[datetime] = None


class MealLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    meal_name: str
    description: Optional[str]
    timestamp: datetime
    calories: float
    carbohydrates: float
    protein: float
    fat: float
    sugar: float
    sodium: float
    fiber: float
    source: str


class NutrientBreakdown(BaseModel):
    calories_kcal: float = 0.0
    carbohydrates_g: float = 0.0
    protein_g: float = 0.0
    fat_g: float = 0.0
    sugar_g: float = 0.0
    sodium_mg: float = 0.0
    fiber_g: float = 0.0


class DietSummaryResponse(BaseModel):
    disclaimer: str = (
        "This estimate only reflects foods recorded by the system and manually logged meals. "
        "It is not a complete measure of total dietary intake and is for lifestyle awareness, not medical advice."
    )
    period: str = "today"  # today, 7d, 30d
    days_analyzed: int = 1
    tracked_pantry_intake: NutrientBreakdown
    manual_logged_intake: NutrientBreakdown
    total_combined_intake: NutrientBreakdown
    dietary_pattern: str  # NORMAL, HIGH_SUGAR, HIGH_SODIUM, HIGH_FAT, INCREASING_CONSUMPTION, IRREGULAR, INSUFFICIENT_DATA
    dietary_pattern_description: str
    per_item_calories: Dict[str, float] = {}


class DailyNutritionTrend(BaseModel):
    date: str
    calories: float
    carbohydrates: float
    protein: float
    fat: float
    sugar: float
    sodium: float
    source: str = "combined"


# ===================================================
# PREDICTION & FORECASTING SCHEMAS
# ===================================================

class ItemPredictionResponse(BaseModel):
    item_id: int
    item_name: str
    unit: str
    current_quantity: float
    historical_average_daily: Optional[float]
    predicted_daily_consumption: float
    predicted_7d_consumption: float
    predicted_14d_consumption: float
    predicted_30d_consumption: float
    remaining_days_math: Optional[float]
    remaining_days_ml: Optional[float]
    predicted_depletion_date: Optional[str]
    prediction_range_90_low: float
    prediction_range_90_high: float
    model_used: str
    stock_status: str


# ===================================================
# RECIPE SCHEMAS
# ===================================================

class RecipeIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_name: str
    item_id: Optional[int] = None
    quantity_per_serving: float
    scaled_quantity: float
    unit: str
    is_pantry_item: bool
    current_stock: Optional[float] = None
    is_in_stock: bool = True


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category: str
    prep_time_minutes: int
    base_servings: int
    target_servings: int
    instructions: str
    estimated_calories_per_serving: float
    total_estimated_calories: float
    tags: List[str] = []
    dietary_attributes: List[str] = []
    can_cook: bool = True
    missing_ingredients_count: int = 0
    pantry_clearer: bool = False
    ingredients: List[RecipeIngredientResponse] = []


class RecipeRecommendationsResponse(BaseModel):
    family_size: int
    ready_to_cook: List[RecipeResponse] = []
    missing_ingredients: List[RecipeResponse] = []
    pantry_clearers: List[RecipeResponse] = []
    healthier_alternatives: List[RecipeResponse] = []


# ===================================================
# SHOPPING / GROCERY LIST SCHEMAS
# ===================================================

class ShoppingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: Optional[int]
    item_name: str
    current_quantity: float
    suggested_quantity: float
    unit: str
    priority: str  # URGENT, HIGH, MEDIUM, LOW
    reason: str
    status: str    # PENDING, PURCHASED
    predicted_depletion_days: Optional[float]
    created_at: datetime
    updated_at: datetime


class ShoppingItemCreate(BaseModel):
    item_name: str
    item_id: Optional[int] = None
    suggested_quantity: float = Field(..., ge=0)
    unit: str = "g"
    priority: str = "MEDIUM"
    reason: str = "Manual restock request"


# ===================================================
# ALERT SCHEMAS
# ===================================================

class AlertLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    item_id: Optional[int]
    item_name: Optional[str]
    alert_type: str
    severity: str
    message: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    timestamp: datetime


# ===================================================
# ML EVALUATION & BENCHMARK SCHEMAS
# ===================================================

class ModelMetrics(BaseModel):
    model_name: str
    mae: float
    rmse: float
    r2: float
    is_baseline: bool = False


class ClassifierMetrics(BaseModel):
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    classes: List[str] = []
    confusion_matrix: List[List[int]] = []


class MLEvaluationResponse(BaseModel):
    notice: str = (
        "This evaluation is performed on synthetically generated multi-household pantry data "
        "using a strict chronological 70/15/15 train/val/test split to prevent time-series leakage. "
        "It must not be represented as real human household measurements."
    )
    dataset_size_records: int
    households_count: int
    train_size: int
    val_size: int
    test_size: int
    regression_benchmarks: List[ModelMetrics] = []
    classification_metrics: Optional[ClassifierMetrics] = None
    feature_importance: Dict[str, float] = {}
    trained_at: Optional[str] = None
