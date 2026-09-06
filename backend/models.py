from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base


def utc_now():
    """Return current UTC datetime (timezone-aware converted to naive or standard UTC)."""
    return datetime.now(timezone.utc)


class HouseholdProfile(Base):
    __tablename__ = "household_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    household_name = Column(String, default="My Household", nullable=False)
    family_size = Column(Integer, default=4, nullable=False)
    adults_count = Column(Integer, default=2, nullable=False)
    children_count = Column(Integer, default=2, nullable=False)
    elderly_count = Column(Integer, default=0, nullable=False)
    activity_profile = Column(String, default="MODERATE", nullable=False)  # SEDENTARY, MODERATE, ACTIVE
    dietary_preference = Column(String, default="BALANCED", nullable=False)  # BALANCED, LOW_SUGAR, LOW_SODIUM, VEGETARIAN

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    items = relationship("Item", back_populates="household")
    meals = relationship("MealLog", back_populates="household", cascade="all, delete-orphan")
    alerts = relationship("AlertLog", back_populates="household", cascade="all, delete-orphan")
    shopping_items = relationship("ShoppingItem", back_populates="household", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<HouseholdProfile(id={self.id}, name='{self.household_name}', family_size={self.family_size})>"


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    household_id = Column(Integer, ForeignKey("household_profiles.id", ondelete="SET NULL"), nullable=True, default=1, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    unit = Column(String, default="g", nullable=False)
    initial_quantity = Column(Float, nullable=False)
    current_quantity = Column(Float, nullable=False)
    minimum_quantity = Column(Float, nullable=False)
    high_intake_threshold = Column(Float, nullable=False)
    
    # Flexible field reserved for future RFID container integration
    rfid_uid = Column(String, nullable=True, unique=True, index=True)

    # Expanded fields for complete nutrition & smart pantry operations
    category = Column(String, default="General", nullable=False)
    serving_size_g = Column(Float, default=50.0, nullable=False)
    calories_per_100g = Column(Float, default=0.0, nullable=False)
    carbohydrates_per_100g = Column(Float, default=0.0, nullable=False)
    protein_per_100g = Column(Float, default=0.0, nullable=False)
    fat_per_100g = Column(Float, default=0.0, nullable=False)
    sugar_per_100g = Column(Float, default=0.0, nullable=False)
    sodium_mg_per_100g = Column(Float, default=0.0, nullable=False)
    fiber_per_100g = Column(Float, default=0.0, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    storage_location = Column(String, nullable=True, default="Pantry Shelf")
    is_perishable = Column(Boolean, default=False, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationship back to HouseholdProfile
    household = relationship("HouseholdProfile", back_populates="items")

    # Relationship to weight readings
    readings = relationship(
        "WeightReading",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="WeightReading.timestamp"
    )

    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', current_quantity={self.current_quantity} {self.unit})>"


class WeightReading(Base):
    __tablename__ = "weight_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    weight = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationship back to Item
    item = relationship("Item", back_populates="readings")

    def __repr__(self):
        return f"<WeightReading(id={self.id}, item_id={self.item_id}, weight={self.weight}, timestamp={self.timestamp})>"


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    household_id = Column(Integer, ForeignKey("household_profiles.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    meal_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    calories = Column(Float, default=0.0, nullable=False)
    carbohydrates = Column(Float, default=0.0, nullable=False)
    protein = Column(Float, default=0.0, nullable=False)
    fat = Column(Float, default=0.0, nullable=False)
    sugar = Column(Float, default=0.0, nullable=False)
    sodium = Column(Float, default=0.0, nullable=False)
    fiber = Column(Float, default=0.0, nullable=False)
    source = Column(String, default="MANUAL", nullable=False)  # MANUAL or EXTERNAL

    household = relationship("HouseholdProfile", back_populates="meals")

    def __repr__(self):
        return f"<MealLog(id={self.id}, name='{self.meal_name}', calories={self.calories})>"


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    category = Column(String, default="Main Course", nullable=False)
    prep_time_minutes = Column(Integer, default=20, nullable=False)
    base_servings = Column(Integer, default=4, nullable=False)
    instructions = Column(String, nullable=False)
    estimated_calories_per_serving = Column(Float, default=0.0, nullable=False)
    tags = Column(String, default="", nullable=False)  # e.g. "Quick, Comfort, Lower Sugar"
    dietary_attributes = Column(String, default="", nullable=False)  # e.g. "Vegetarian, Lower Sodium"
    created_at = Column(DateTime, default=utc_now, nullable=False)

    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}', servings={self.base_servings})>"


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    item_name = Column(String, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    quantity_per_serving = Column(Float, nullable=False)
    unit = Column(String, default="g", nullable=False)
    is_pantry_item = Column(Boolean, default=True, nullable=False)

    recipe = relationship("Recipe", back_populates="ingredients")
    item = relationship("Item")

    def __repr__(self):
        return f"<RecipeIngredient(recipe_id={self.recipe_id}, item='{self.item_name}', qty={self.quantity_per_serving})>"


class ShoppingItem(Base):
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    household_id = Column(Integer, ForeignKey("household_profiles.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True, index=True)
    item_name = Column(String, nullable=False)
    current_quantity = Column(Float, default=0.0, nullable=False)
    suggested_quantity = Column(Float, nullable=False)
    unit = Column(String, default="g", nullable=False)
    priority = Column(String, default="MEDIUM", nullable=False)  # URGENT, HIGH, MEDIUM, LOW
    reason = Column(String, nullable=False)
    status = Column(String, default="PENDING", nullable=False)  # PENDING, PURCHASED
    predicted_depletion_days = Column(Float, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    household = relationship("HouseholdProfile", back_populates="shopping_items")
    item = relationship("Item")

    def __repr__(self):
        return f"<ShoppingItem(id={self.id}, item='{self.item_name}', status='{self.status}')>"


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    household_id = Column(Integer, ForeignKey("household_profiles.id", ondelete="CASCADE"), nullable=False, default=1, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=True, index=True)
    item_name = Column(String, nullable=True)
    alert_type = Column(String, nullable=False, index=True)  # LOW_STOCK, OUT_OF_STOCK, HIGH_CONSUMPTION, UNUSUAL_CONSUMPTION, PREDICTED_STOCKOUT, etc.
    severity = Column(String, default="WARNING", nullable=False)  # CRITICAL, WARNING, INFO
    message = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    household = relationship("HouseholdProfile", back_populates="alerts")
    item = relationship("Item")

    def __repr__(self):
        return f"<AlertLog(id={self.id}, type='{self.alert_type}', item='{self.item_name}', resolved={self.is_resolved})>"
