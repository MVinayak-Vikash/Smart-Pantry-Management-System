import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend import crud, models
from backend.alerts.engine import evaluate_and_sync_alerts


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


def test_alert_generation_and_severities(db_session):
    """Verify that low stock and out of stock generate warning/critical alerts."""
    # Set Rice to 800g (below 1000g min -> LOW_STOCK)
    rice = db_session.query(models.Item).filter(models.Item.name == "Rice").first()
    rice.current_quantity = 800.0

    # Set Sugar to 0g (OUT_OF_STOCK)
    sugar = db_session.query(models.Item).filter(models.Item.name == "Sugar").first()
    sugar.current_quantity = 0.0
    db_session.commit()

    alerts = evaluate_and_sync_alerts(db_session, household_id=1)
    alert_types = [a.alert_type for a in alerts]

    assert "OUT_OF_STOCK" in alert_types
    assert "LOW_STOCK" in alert_types

    out_alert = next(a for a in alerts if a.alert_type == "OUT_OF_STOCK")
    assert out_alert.severity == "CRITICAL"

    low_alert = next(a for a in alerts if a.alert_type == "LOW_STOCK")
    assert low_alert.severity == "WARNING"


def test_alert_deduplication_within_24_hours(db_session):
    """Calling alert sync multiple times must not spam duplicate records."""
    rice = db_session.query(models.Item).filter(models.Item.name == "Rice").first()
    rice.current_quantity = 500.0
    db_session.commit()

    # First sync
    alerts1 = evaluate_and_sync_alerts(db_session, household_id=1)
    count1 = len(alerts1)
    assert count1 > 0

    # Second sync (simulating page reload)
    alerts2 = evaluate_and_sync_alerts(db_session, household_id=1)
    count2 = len(alerts2)
    assert count2 == count1

    # Total alert rows in database must equal count1
    all_rows = db_session.query(models.AlertLog).all()
    assert len(all_rows) == count1


def test_alert_resolution_lifecycle(db_session):
    """Test resolving an alert."""
    rice = db_session.query(models.Item).filter(models.Item.name == "Rice").first()
    rice.current_quantity = 500.0
    db_session.commit()

    alerts = evaluate_and_sync_alerts(db_session, household_id=1)
    assert len(alerts) > 0
    target_id = alerts[0].id

    resolved = crud.resolve_alert(db_session, target_id)
    assert resolved.is_resolved is True
    assert resolved.resolved_at is not None

    # Unresolved alerts query should no longer include target_id
    active = crud.get_alerts(db_session, household_id=1, unresolved_only=True)
    assert target_id not in [a.id for a in active]
