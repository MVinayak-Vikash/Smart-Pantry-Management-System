import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend import crud, schemas, models


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
    yield db
    db.close()


def test_household_schema_demographic_sum_validation():
    """Verify that adults + children + elderly must equal family_size."""
    # Valid
    valid = schemas.HouseholdProfileCreate(
        household_name="Sharma Family",
        family_size=5,
        adults_count=2,
        children_count=2,
        elderly_count=1,
        activity_profile="MODERATE",
        dietary_preference="BALANCED"
    )
    assert valid.family_size == 5

    # Invalid: sum is 3 != 5
    with pytest.raises(ValidationError) as exc:
        schemas.HouseholdProfileCreate(
            household_name="Invalid Family",
            family_size=5,
            adults_count=2,
            children_count=1,
            elderly_count=0,
            activity_profile="MODERATE",
            dietary_preference="BALANCED"
        )
    assert "Demographic sum" in str(exc.value)


def test_household_schema_family_size_minimum():
    """Family size must be at least 1."""
    with pytest.raises(ValidationError):
        schemas.HouseholdProfileCreate(
            household_name="Empty Family",
            family_size=0,
            adults_count=0,
            children_count=0,
            elderly_count=0,
        )


def test_household_crud_lifecycle(db_session):
    """Test seed, retrieve, and update household profile in SQLite."""
    profile = crud.get_household_profile(db_session, household_id=1)
    assert profile is not None
    assert profile.family_size == 4
    assert profile.household_name == "My Household"

    # Update profile
    updated = crud.update_household_profile(
        db_session,
        data={
            "household_name": "Vikash Residence",
            "family_size": 3,
            "adults_count": 2,
            "children_count": 1,
            "elderly_count": 0,
            "dietary_preference": "LOW_SUGAR"
        },
        household_id=1
    )
    assert updated.household_name == "Vikash Residence"
    assert updated.family_size == 3
    assert updated.dietary_preference == "LOW_SUGAR"

    # Retrieve again
    fetched = crud.get_household_profile(db_session, household_id=1)
    assert fetched.household_name == "Vikash Residence"
    assert fetched.family_size == 3
