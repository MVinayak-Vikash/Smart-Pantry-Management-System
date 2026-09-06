from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models import (
    Item, WeightReading, HouseholdProfile, MealLog,
    Recipe, RecipeIngredient, ShoppingItem, AlertLog, utc_now
)
from backend import calculations


DEFAULT_ITEMS = [
    {
        "name": "Rice",
        "unit": "g",
        "initial_quantity": 5000.0,
        "current_quantity": 5000.0,
        "minimum_quantity": 1000.0,
        "high_intake_threshold": 300.0,  # g/day configurable threshold
        "category": "Grains & Cereals",
        "serving_size_g": 60.0,
        "calories_per_100g": 365.0,
        "carbohydrates_per_100g": 80.0,
        "protein_per_100g": 7.1,
        "fat_per_100g": 0.7,
        "sugar_per_100g": 0.1,
        "sodium_mg_per_100g": 5.0,
        "fiber_per_100g": 1.3,
        "storage_location": "Pantry Bin A1",
        "is_perishable": False,
        "active": True,
    },
    {
        "name": "Sugar",
        "unit": "g",
        "initial_quantity": 2000.0,
        "current_quantity": 2000.0,
        "minimum_quantity": 500.0,
        "high_intake_threshold": 50.0,   # g/day configurable threshold
        "category": "Sweeteners",
        "serving_size_g": 15.0,
        "calories_per_100g": 387.0,
        "carbohydrates_per_100g": 100.0,
        "protein_per_100g": 0.0,
        "fat_per_100g": 0.0,
        "sugar_per_100g": 100.0,
        "sodium_mg_per_100g": 2.0,
        "fiber_per_100g": 0.0,
        "storage_location": "Spice Rack Top",
        "is_perishable": False,
        "active": True,
    },
    {
        "name": "Salt",
        "unit": "g",
        "initial_quantity": 1000.0,
        "current_quantity": 1000.0,
        "minimum_quantity": 250.0,
        "high_intake_threshold": 5.0,    # g/day configurable threshold
        "category": "Seasoning",
        "serving_size_g": 5.0,
        "calories_per_100g": 0.0,
        "carbohydrates_per_100g": 0.0,
        "protein_per_100g": 0.0,
        "fat_per_100g": 0.0,
        "sugar_per_100g": 0.0,
        "sodium_mg_per_100g": 38758.0,
        "fiber_per_100g": 0.0,
        "storage_location": "Spice Rack Middle",
        "is_perishable": False,
        "active": True,
    },
    {
        "name": "Ghee",
        "unit": "g",
        "initial_quantity": 1000.0,
        "current_quantity": 1000.0,
        "minimum_quantity": 250.0,
        "high_intake_threshold": 30.0,   # g/day configurable threshold
        "category": "Oils & Healthy Fats",
        "serving_size_g": 15.0,
        "calories_per_100g": 900.0,
        "carbohydrates_per_100g": 0.0,
        "protein_per_100g": 0.0,
        "fat_per_100g": 99.5,
        "sugar_per_100g": 0.0,
        "sodium_mg_per_100g": 0.0,
        "fiber_per_100g": 0.0,
        "storage_location": "Cool Dark Shelf",
        "is_perishable": False,
        "active": True,
    },
]

INITIAL_RECIPES = [
    {
        "name": "Classic Khichdi",
        "description": "Wholesome, comforting staple made of rice seasoned with fragrant ghee and salt.",
        "category": "Main Course",
        "prep_time_minutes": 25,
        "base_servings": 4,
        "instructions": "1. Rinse rice thoroughly. 2. Boil with 3 cups of water and salt until soft. 3. Finish with warm melted ghee.",
        "estimated_calories_per_serving": 285.0,
        "tags": "Comfort, Quick, Staple, Hearty",
        "dietary_attributes": "Vegetarian, Gluten-Free",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 60.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 10.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.5, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Cardamom Rice Kheer",
        "description": "Rich traditional rice dessert sweetened with sugar and finished with aromatic ghee.",
        "category": "Dessert",
        "prep_time_minutes": 35,
        "base_servings": 4,
        "instructions": "1. Simmer rice in milk until tender. 2. Stir in sugar until dissolved. 3. Garnish with warm ghee and cardamom.",
        "estimated_calories_per_serving": 270.0,
        "tags": "Sweet, Festive, Dessert",
        "dietary_attributes": "Vegetarian",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 40.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Sugar", "quantity_per_serving": 25.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 5.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Fragrant Ghee Rice",
        "description": "Aromatic tempered rice dish made with generous spoonfuls of golden ghee and balanced salt.",
        "category": "Main Course",
        "prep_time_minutes": 20,
        "base_servings": 4,
        "instructions": "1. Cook rice until fluffy. 2. Warm ghee in pan and gently fold through warm rice with salt.",
        "estimated_calories_per_serving": 380.0,
        "tags": "Aromatic, Quick, Comfort",
        "dietary_attributes": "Vegetarian",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 70.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 15.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.5, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Salted Rice Porridge (Congee)",
        "description": "Gentle, easily digestible breakfast porridge with a pinch of seasoning.",
        "category": "Breakfast",
        "prep_time_minutes": 30,
        "base_servings": 2,
        "instructions": "1. Simmer rice in 5 parts water until creamy. 2. Season with pinch of salt.",
        "estimated_calories_per_serving": 185.0,
        "tags": "Light, Recovery, Easy Digest, Lower Fat",
        "dietary_attributes": "Vegan, Low Fat",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 50.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Sweet Rice Halwa",
        "description": "Rich pan-roasted rice sweet infused with ghee and caramelized sugar.",
        "category": "Dessert",
        "prep_time_minutes": 25,
        "base_servings": 4,
        "instructions": "1. Roast rice flour in ghee until fragrant. 2. Add hot sugar syrup and stir until glossy.",
        "estimated_calories_per_serving": 360.0,
        "tags": "Rich, Traditional, Sweet",
        "dietary_attributes": "Vegetarian",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 50.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Sugar", "quantity_per_serving": 30.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 20.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Low-Sodium Steamed Rice Bowl",
        "description": "Light steamed rice finished with a light touch of ghee without added sodium.",
        "category": "Healthy / Special",
        "prep_time_minutes": 20,
        "base_servings": 2,
        "instructions": "1. Steam rice in fresh water. 2. Drizzle tiny spoon of ghee.",
        "estimated_calories_per_serving": 310.0,
        "tags": "Lower Sodium, Clean, Diet",
        "dietary_attributes": "Vegetarian, Lower Sodium",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 75.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 5.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Sugar-Free Rice & Ghee Snack",
        "description": "Simple savory snack with toasted rice grains, ghee, and minimal salt.",
        "category": "Snack",
        "prep_time_minutes": 15,
        "base_servings": 2,
        "instructions": "1. Toast cooked rice with ghee and light salt until slightly crisp.",
        "estimated_calories_per_serving": 270.0,
        "tags": "Lower Sugar, Quick, Savory",
        "dietary_attributes": "Vegetarian, Lower Sugar",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 60.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 8.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 1.5, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Lemon Turmeric Rice",
        "description": "Zesty seasoned rice with golden turmeric, ghee, and light salt tempering.",
        "category": "Lunch",
        "prep_time_minutes": 20,
        "base_servings": 4,
        "instructions": "1. Cook rice. 2. Warm ghee with pinch of turmeric and salt, toss gently.",
        "estimated_calories_per_serving": 310.0,
        "tags": "Tangy, Colorful, Quick",
        "dietary_attributes": "Vegetarian",
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 65.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 10.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.5, "unit": "g", "is_pantry_item": True},
        ],
    },
]


# ===================================================
# HOUSEHOLD CRUD & SEEDING
# ===================================================

def seed_default_household(db: Session) -> HouseholdProfile:
    """Ensure a default household profile exists."""
    profile = db.query(HouseholdProfile).filter(HouseholdProfile.id == 1).first()
    if not profile:
        profile = HouseholdProfile(
            id=1,
            household_name="My Household",
            family_size=4,
            adults_count=2,
            children_count=2,
            elderly_count=0,
            activity_profile="MODERATE",
            dietary_preference="BALANCED",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def get_household_profile(db: Session, household_id: int = 1) -> HouseholdProfile:
    """Retrieve household profile or create default if none exists."""
    profile = db.query(HouseholdProfile).filter(HouseholdProfile.id == household_id).first()
    if not profile:
        profile = seed_default_household(db)
    return profile


def update_household_profile(db: Session, data: Dict[str, Any], household_id: int = 1) -> HouseholdProfile:
    """Update household profile attributes."""
    profile = get_household_profile(db, household_id)
    for key, value in data.items():
        if value is not None and hasattr(profile, key):
            setattr(profile, key, value)
    profile.updated_at = utc_now()
    db.commit()
    db.refresh(profile)
    return profile


# ===================================================
# ITEMS CRUD & SEEDING
# ===================================================

def seed_initial_items(db: Session) -> List[Item]:
    """Ensure the four default staple items exist in the database with nutritional metadata."""
    items = []
    for item_data in DEFAULT_ITEMS:
        existing = db.query(Item).filter(Item.name == item_data["name"]).first()
        if not existing:
            item = Item(**item_data)
            db.add(item)
            db.commit()
            db.refresh(item)
            items.append(item)
        else:
            # Update missing attributes on existing items if any
            updated = False
            for k, v in item_data.items():
                if getattr(existing, k, None) is None or getattr(existing, k, None) == 0.0:
                    setattr(existing, k, v)
                    updated = True
            if updated:
                db.commit()
                db.refresh(existing)
            items.append(existing)
    return items


def seed_sample_readings(db: Session) -> Dict[str, Any]:
    """
    Seed realistic multi-day sample readings for demonstration:
      - Rice: 5000, 4750, 4500, 4250, 4000, 3750 (5 consumption days of 250g/day -> Normal)
      - Sugar: 2000, 1950, 1900, 1850, 1800 (4 consumption days of 50g/day -> Normal)
      - Salt: 1000, 990, 980, 970, 960 (4 consumption days of 10g/day > 5g/day threshold -> High)
      - Ghee: 1000, 970, 940, 910, 880 (4 consumption days of 30g/day -> Normal)
    """
    seed_initial_items(db)

    sample_series = {
        "Rice": [5000.0, 4750.0, 4500.0, 4250.0, 4000.0, 3750.0],
        "Sugar": [2000.0, 1950.0, 1900.0, 1850.0, 1800.0],
        "Salt": [1000.0, 990.0, 980.0, 970.0, 960.0],
        "Ghee": [1000.0, 970.0, 940.0, 910.0, 880.0],
    }

    base_date = datetime.now(timezone.utc) - timedelta(days=6)
    total_added = 0

    for name, weights in sample_series.items():
        item = db.query(Item).filter(Item.name == name).first()
        if not item:
            continue

        # Remove existing readings for a clean baseline seed
        db.query(WeightReading).filter(WeightReading.item_id == item.id).delete()

        # Add readings 1 day apart
        for day_offset, weight in enumerate(weights):
            reading_time = base_date + timedelta(days=day_offset, hours=9)
            reading = WeightReading(
                item_id=item.id,
                weight=weight,
                timestamp=reading_time
            )
            db.add(reading)
            total_added += 1

        # Update item's current quantity to the latest reading
        item.current_quantity = weights[-1]
        item.updated_at = datetime.now(timezone.utc)
        db.commit()

    return {"message": "Simulated sample readings seeded successfully", "readings_count": total_added}


def get_items(db: Session, active_only: bool = True) -> List[Item]:
    """Retrieve items ordered by id."""
    query = db.query(Item)
    if active_only:
        query = query.filter(Item.active == True)
    return query.order_by(Item.id.asc()).all()


def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    """Retrieve an item by id."""
    return db.query(Item).filter(Item.id == item_id).first()


def get_item_by_name(db: Session, name: str) -> Optional[Item]:
    """Retrieve an item by name."""
    return db.query(Item).filter(Item.name == name).first()


def get_item_by_rfid(db: Session, rfid_uid: str) -> Optional[Item]:
    """Retrieve an item by its RFID tag UID."""
    return db.query(Item).filter(Item.rfid_uid == rfid_uid).first()


def create_item(db: Session, item_data: Dict[str, Any]) -> Item:
    """Create a new custom pantry item."""
    if "current_quantity" not in item_data or item_data["current_quantity"] is None:
        item_data["current_quantity"] = item_data.get("initial_quantity", 1000.0)
    item = Item(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item_id: int, update_data: Dict[str, Any]) -> Optional[Item]:
    """Update item metadata or thresholds."""
    item = get_item_by_id(db, item_id)
    if not item:
        return None
    for k, v in update_data.items():
        if v is not None and hasattr(item, k):
            setattr(item, k, v)
    item.updated_at = utc_now()
    db.commit()
    db.refresh(item)
    return item


def create_weight_reading(
    db: Session,
    item_id: int,
    weight: float,
    timestamp: Optional[datetime] = None
) -> Optional[WeightReading]:
    """
    Record a new weight reading, update the item's current_quantity and updated_at.
    Returns the created WeightReading, or None if the item does not exist.
    """
    item = get_item_by_id(db, item_id)
    if not item:
        return None

    reading_timestamp = timestamp or utc_now()
    reading = WeightReading(
        item_id=item.id,
        weight=weight,
        timestamp=reading_timestamp
    )
    db.add(reading)

    # Update item quantity and timestamp
    item.current_quantity = weight
    item.updated_at = utc_now()

    db.commit()
    db.refresh(reading)
    db.refresh(item)
    return reading


def compute_item_metrics(item: Item) -> Dict[str, Any]:
    """
    Calculate derived statuses and metrics for an item based on its historical readings.
    """
    readings_data = [
        {"id": r.id, "weight": r.weight, "timestamp": r.timestamp}
        for r in item.readings
    ]

    avail_status = calculations.calculate_availability_status(
        item.current_quantity,
        item.minimum_quantity
    )

    avg_intake, days_with_data = calculations.calculate_average_daily_intake(readings_data)

    intake_status = calculations.calculate_intake_status(
        avg_intake,
        item.high_intake_threshold
    )

    rem_days = calculations.calculate_remaining_days(
        item.current_quantity,
        avg_intake
    )

    return {
        "id": item.id,
        "name": item.name,
        "unit": item.unit,
        "initial_quantity": item.initial_quantity,
        "current_quantity": item.current_quantity,
        "minimum_quantity": item.minimum_quantity,
        "high_intake_threshold": item.high_intake_threshold,
        "availability_status": avail_status,
        "average_daily_intake": avg_intake,
        "intake_status": intake_status,
        "remaining_days": rem_days,
        "days_with_data": days_with_data,
        "rfid_uid": item.rfid_uid,
        "category": item.category,
        "serving_size_g": item.serving_size_g,
        "calories_per_100g": item.calories_per_100g,
        "carbohydrates_per_100g": item.carbohydrates_per_100g,
        "protein_per_100g": item.protein_per_100g,
        "fat_per_100g": item.fat_per_100g,
        "sugar_per_100g": item.sugar_per_100g,
        "sodium_mg_per_100g": item.sodium_mg_per_100g,
        "fiber_per_100g": item.fiber_per_100g,
        "expiry_date": item.expiry_date,
        "storage_location": item.storage_location,
        "is_perishable": item.is_perishable,
        "active": item.active,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def get_item_consumption_history(db: Session, item_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve item consumption events, refill amounts, and summary intake metrics.
    """
    item = get_item_by_id(db, item_id)
    if not item:
        return None

    readings_data = [
        {"id": r.id, "weight": r.weight, "timestamp": r.timestamp}
        for r in item.readings
    ]

    intervals = calculations.calculate_consumption_intervals(readings_data)
    avg_intake, days_with_data = calculations.calculate_average_daily_intake(readings_data)

    total_consumption = round(sum(i["consumption"] for i in intervals), 2)
    total_refill = round(sum(i["refill_amount"] for i in intervals), 2)

    return {
        "item_id": item.id,
        "item_name": item.name,
        "unit": item.unit,
        "records": intervals,
        "total_consumption": total_consumption,
        "total_refill": total_refill,
        "days_with_data": days_with_data,
        "average_daily_intake": avg_intake,
    }


# ===================================================
# RECIPES CRUD & SEEDING
# ===================================================

def seed_initial_recipes(db: Session) -> List[Recipe]:
    """Seed base recipes with ingredients if not already present."""
    recipes = []
    for r_data in INITIAL_RECIPES:
        existing = db.query(Recipe).filter(Recipe.name == r_data["name"]).first()
        if not existing:
            ingredients_data = r_data.get("ingredients", [])
            recipe_kwargs = {k: v for k, v in r_data.items() if k != "ingredients"}
            recipe = Recipe(**recipe_kwargs)
            db.add(recipe)
            db.commit()
            db.refresh(recipe)

            for ing in ingredients_data:
                # Map to Item.id if item exists
                pantry_item = db.query(Item).filter(Item.name == ing["item_name"]).first()
                item_id = pantry_item.id if pantry_item else None
                rec_ing = RecipeIngredient(
                    recipe_id=recipe.id,
                    item_name=ing["item_name"],
                    item_id=item_id,
                    quantity_per_serving=ing["quantity_per_serving"],
                    unit=ing.get("unit", "g"),
                    is_pantry_item=ing.get("is_pantry_item", True),
                )
                db.add(rec_ing)
            db.commit()
            recipes.append(recipe)
        else:
            recipes.append(existing)
    return recipes


def get_recipes(db: Session) -> List[Recipe]:
    """Retrieve all recipes ordered by id."""
    return db.query(Recipe).order_by(Recipe.id.asc()).all()


def get_recipe_by_id(db: Session, recipe_id: int) -> Optional[Recipe]:
    """Retrieve a recipe with its ingredients."""
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


# ===================================================
# MEAL LOGGING CRUD
# ===================================================

def create_meal_log(db: Session, meal_data: Dict[str, Any], household_id: int = 1) -> MealLog:
    """Create a manual external meal record."""
    meal = MealLog(household_id=household_id, **meal_data)
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def get_meal_logs(db: Session, household_id: int = 1, limit: int = 50) -> List[MealLog]:
    """Retrieve recent manual meal logs."""
    return (
        db.query(MealLog)
        .filter(MealLog.household_id == household_id)
        .order_by(MealLog.timestamp.desc())
        .limit(limit)
        .all()
    )


# ===================================================
# SHOPPING LIST CRUD
# ===================================================

def get_shopping_items(db: Session, household_id: int = 1) -> List[ShoppingItem]:
    """Retrieve shopping items ordered by priority and status."""
    return (
        db.query(ShoppingItem)
        .filter(ShoppingItem.household_id == household_id)
        .order_by(ShoppingItem.status.asc(), ShoppingItem.id.asc())
        .all()
    )


def create_or_update_shopping_item(db: Session, data: Dict[str, Any], household_id: int = 1) -> ShoppingItem:
    """Add or update an item on the shopping restock list."""
    item_id = data.get("item_id")
    item_name = data.get("item_name")

    existing = None
    if item_id:
        existing = (
            db.query(ShoppingItem)
            .filter(ShoppingItem.household_id == household_id, ShoppingItem.item_id == item_id, ShoppingItem.status == "PENDING")
            .first()
        )
    elif item_name:
        existing = (
            db.query(ShoppingItem)
            .filter(ShoppingItem.household_id == household_id, ShoppingItem.item_name == item_name, ShoppingItem.status == "PENDING")
            .first()
        )

    if existing:
        existing.suggested_quantity = data.get("suggested_quantity", existing.suggested_quantity)
        existing.priority = data.get("priority", existing.priority)
        existing.reason = data.get("reason", existing.reason)
        existing.current_quantity = data.get("current_quantity", existing.current_quantity)
        existing.predicted_depletion_days = data.get("predicted_depletion_days", existing.predicted_depletion_days)
        existing.updated_at = utc_now()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_item = ShoppingItem(household_id=household_id, **data)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item


def mark_shopping_item_purchased(db: Session, shopping_item_id: int, record_refill: bool = True) -> Optional[ShoppingItem]:
    """Mark shopping item as purchased and optionally record refill weight in the item container."""
    item = db.query(ShoppingItem).filter(ShoppingItem.id == shopping_item_id).first()
    if not item:
        return None

    item.status = "PURCHASED"
    item.updated_at = utc_now()

    if record_refill and item.item_id:
        pantry_item = get_item_by_id(db, item.item_id)
        if pantry_item:
            new_weight = pantry_item.current_quantity + item.suggested_quantity
            create_weight_reading(db, item.item_id, new_weight)

    db.commit()
    db.refresh(item)
    return item


# ===================================================
# ALERTS CRUD
# ===================================================

def get_alerts(db: Session, household_id: int = 1, unresolved_only: bool = False) -> List[AlertLog]:
    """Retrieve alerts ordered by timestamp descending."""
    query = db.query(AlertLog).filter(AlertLog.household_id == household_id)
    if unresolved_only:
        query = query.filter(AlertLog.is_resolved == False)
    return query.order_by(AlertLog.timestamp.desc()).all()


def create_alert_deduplicated(db: Session, data: Dict[str, Any], household_id: int = 1) -> Optional[AlertLog]:
    """
    Create a new alert only if an identical unresolved alert does not already exist
    within the past 24 hours. Prevents notification flooding.
    """
    item_id = data.get("item_id")
    alert_type = data.get("alert_type")
    cutoff = utc_now() - timedelta(hours=24)

    existing = (
        db.query(AlertLog)
        .filter(
            AlertLog.household_id == household_id,
            AlertLog.item_id == item_id,
            AlertLog.alert_type == alert_type,
            AlertLog.is_resolved == False,
            AlertLog.timestamp >= cutoff
        )
        .first()
    )

    if existing:
        # Update timestamp to avoid stale alerts without spamming duplicate records
        existing.timestamp = utc_now()
        existing.message = data.get("message", existing.message)
        db.commit()
        db.refresh(existing)
        return existing

    new_alert = AlertLog(household_id=household_id, **data)
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert


def resolve_alert(db: Session, alert_id: int) -> Optional[AlertLog]:
    """Mark an alert as resolved."""
    alert = db.query(AlertLog).filter(AlertLog.id == alert_id).first()
    if not alert:
        return None
    alert.is_resolved = True
    alert.resolved_at = utc_now()
    db.commit()
    db.refresh(alert)
    return alert
