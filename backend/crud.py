from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Item, WeightReading, utc_now
from backend import calculations


DEFAULT_ITEMS = [
    {
        "name": "Rice",
        "unit": "g",
        "initial_quantity": 5000.0,
        "current_quantity": 5000.0,
        "minimum_quantity": 1000.0,
        "high_intake_threshold": 300.0,  # g/day configurable threshold
    },
    {
        "name": "Sugar",
        "unit": "g",
        "initial_quantity": 2000.0,
        "current_quantity": 2000.0,
        "minimum_quantity": 500.0,
        "high_intake_threshold": 50.0,   # g/day configurable threshold
    },
    {
        "name": "Salt",
        "unit": "g",
        "initial_quantity": 1000.0,
        "current_quantity": 1000.0,
        "minimum_quantity": 250.0,
        "high_intake_threshold": 5.0,    # g/day configurable threshold
    },
    {
        "name": "Ghee",
        "unit": "g",
        "initial_quantity": 1000.0,
        "current_quantity": 1000.0,
        "minimum_quantity": 250.0,
        "high_intake_threshold": 30.0,   # g/day configurable threshold
    },
]


def seed_initial_items(db: Session) -> List[Item]:
    """Ensure the four default staple items exist in the database."""
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
    # First make sure items exist
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


def get_items(db: Session) -> List[Item]:
    """Retrieve all items ordered by id."""
    return db.query(Item).order_by(Item.id.asc()).all()


def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    """Retrieve an item by id."""
    return db.query(Item).filter(Item.id == item_id).first()


def get_item_by_name(db: Session, name: str) -> Optional[Item]:
    """Retrieve an item by name."""
    return db.query(Item).filter(Item.name == name).first()


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
