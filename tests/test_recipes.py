import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend import crud, models
from backend.recipes.engine import evaluate_recipe_recommendations


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
    crud.seed_initial_recipes(db)
    yield db
    db.close()


def test_recipe_family_size_scaling(db_session):
    """Verify that required ingredients scale dynamically with family size."""
    # Set family size to 6
    crud.update_household_profile(db_session, {"family_size": 6, "adults_count": 4, "children_count": 2}, household_id=1)

    recs = evaluate_recipe_recommendations(db_session, household_id=1)
    assert recs["family_size"] == 6

    # Khichdi has base servings 4, Rice quantity 60g / serving.
    # For family of 6, scaled_quantity = 60 * 6 = 360g.
    khichdi = next((r for r in recs["ready_to_cook"] if r["name"] == "Classic Khichdi"), None)
    assert khichdi is not None
    rice_ing = next(i for i in khichdi["ingredients"] if i["item_name"] == "Rice")
    assert rice_ing["scaled_quantity"] == 360.0


def test_recipe_missing_ingredients_categorization(db_session):
    """Verify that recipes requiring unavailable items are sorted into missing_ingredients."""
    # Drain Ghee to 0g
    ghee = db_session.query(models.Item).filter(models.Item.name == "Ghee").first()
    ghee.current_quantity = 0.0
    db_session.commit()

    recs = evaluate_recipe_recommendations(db_session, household_id=1)

    # Khichdi requires Ghee -> must now be in missing_ingredients
    missing_names = [r["name"] for r in recs["missing_ingredients"]]
    assert "Classic Khichdi" in missing_names

    # Salted Rice Porridge only requires Rice + Salt -> must remain in ready_to_cook
    ready_names = [r["name"] for r in recs["ready_to_cook"]]
    assert "Salted Rice Porridge (Congee)" in ready_names


def test_pantry_clearer_detection(db_session):
    """Verify that items at low stock trigger the pantry_clearer flag in recipes."""
    # Set Rice to 800g (below 1000g minimum -> LOW)
    rice = db_session.query(models.Item).filter(models.Item.name == "Rice").first()
    rice.current_quantity = 800.0
    db_session.commit()

    recs = evaluate_recipe_recommendations(db_session, household_id=1)
    pantry_clearers = recs["pantry_clearers"]
    assert len(pantry_clearers) > 0
    clearer_names = [r["name"] for r in pantry_clearers]
    assert "Classic Khichdi" in clearer_names or "Salted Rice Porridge (Congee)" in clearer_names
