import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend import crud, models
from backend.shopping.generator import (
    calculate_suggested_purchase,
    generate_restock_recommendations
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    crud.seed_default_household(db)
    crud.seed_initial_items(db)
    yield db
    db.close()


def test_target_stock_level_policy():
    """Verify purchase quantity = max(initial, min * 3) - current."""
    # Rice: initial 5000, min 1000 -> target 5000. Current 800 -> suggested 4200
    suggested = calculate_suggested_purchase(current_quantity=800.0, initial_quantity=5000.0, minimum_quantity=1000.0)
    assert suggested == 4200.0

    # Current exceeds target -> suggested 0
    suggested_zero = calculate_suggested_purchase(current_quantity=6000.0, initial_quantity=5000.0, minimum_quantity=1000.0)
    assert suggested_zero == 0.0


def test_generate_restock_recommendations_triggers(db_session):
    """Verify shopping list items are generated with appropriate priority."""
    # Set Rice to 800g (Low stock)
    rice = db_session.query(models.Item).filter(models.Item.name == "Rice").first()
    rice.current_quantity = 800.0

    # Set Sugar to 0g (Out of stock)
    sugar = db_session.query(models.Item).filter(models.Item.name == "Sugar").first()
    sugar.current_quantity = 0.0
    db_session.commit()

    items = generate_restock_recommendations(db_session, household_id=1)
    item_names = [i.item_name for i in items]

    assert "Rice" in item_names
    assert "Sugar" in item_names

    sugar_shop = next(i for i in items if i.item_name == "Sugar")
    assert sugar_shop.priority == "URGENT"

    rice_shop = next(i for i in items if i.item_name == "Rice")
    assert rice_shop.priority == "HIGH"


def test_mark_shopping_item_purchased(db_session):
    """Verify purchase clears status and logs refill into item."""
    rice = db_session.query(models.Item).filter(models.Item.name == "Rice").first()
    rice.current_quantity = 800.0
    db_session.commit()

    recs = generate_restock_recommendations(db_session, household_id=1)
    rice_rec = next(i for i in recs if i.item_name == "Rice")
    assert rice_rec.status == "PENDING"

    # Mark as purchased
    purchased = crud.mark_shopping_item_purchased(db_session, rice_rec.id, record_refill=True)
    assert purchased.status == "PURCHASED"

    # Verify Rice current_quantity increased
    db_session.refresh(rice)
    assert rice.current_quantity > 800.0
