import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, auto_migrate_sqlite, init_db
from backend import models, crud


def test_sqlite_auto_migration_preserves_data():
    """Verify that adding new columns to an existing SQLite items table preserves existing rows."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # 1. Create old Phase 1 items table schema manually
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR UNIQUE NOT NULL,
                unit VARCHAR NOT NULL,
                initial_quantity FLOAT NOT NULL,
                current_quantity FLOAT NOT NULL,
                minimum_quantity FLOAT NOT NULL,
                high_intake_threshold FLOAT NOT NULL,
                rfid_uid VARCHAR UNIQUE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))
        conn.execute(text("""
            INSERT INTO items (name, unit, initial_quantity, current_quantity, minimum_quantity, high_intake_threshold, created_at, updated_at)
            VALUES ('Rice', 'g', 5000.0, 4800.0, 1000.0, 300.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """))
        conn.commit()

    # 2. Run auto-migration
    auto_migrate_sqlite(engine)

    # 3. Verify columns now exist
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("items")}
    assert "calories_per_100g" in cols
    assert "carbohydrates_per_100g" in cols
    assert "protein_per_100g" in cols
    assert "fat_per_100g" in cols
    assert "sugar_per_100g" in cols
    assert "sodium_mg_per_100g" in cols
    assert "category" in cols
    assert "storage_location" in cols
    assert "is_perishable" in cols
    assert "active" in cols

    # 4. Verify existing row is intact
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name, current_quantity, category FROM items WHERE name='Rice'")).fetchone()
        assert result is not None
        assert result[1] == "Rice"
        assert result[2] == 4800.0
        assert result[3] == "General"


def test_init_db_seeds_all_entities():
    """Verify init_db seeds household, items, and base recipes."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    init_db(target_engine=engine)

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        # Check household
        household = db.query(models.HouseholdProfile).first()
        assert household is not None
        assert household.family_size == 4

        # Check items
        items = db.query(models.Item).all()
        assert len(items) == 4
        names = {i.name for i in items}
        assert names == {"Rice", "Sugar", "Salt", "Ghee"}
        rice = next(i for i in items if i.name == "Rice")
        assert rice.calories_per_100g == 365.0
        assert rice.category == "Grains & Cereals"

        # Check recipes
        recipes = db.query(models.Recipe).all()
        assert len(recipes) >= 5
        recipe_names = {r.name for r in recipes}
        assert "Classic Khichdi" in recipe_names
    finally:
        db.close()
