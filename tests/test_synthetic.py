import pytest
from datetime import datetime, timezone
import pandas as pd
from data.synthetic.generator import (
    generate_household_profiles,
    simulate_household_pantry_history,
    generate_and_save_datasets,
    ITEM_CONFIG
)


def test_generate_household_profiles_reproducibility():
    """Verify deterministic seed produces identical profiles."""
    df1 = generate_household_profiles(num_households=20, seed=42)
    df2 = generate_household_profiles(num_households=20, seed=42)
    pd.testing.assert_frame_equal(df1, df2)
    assert len(df1) == 20
    # Demographic check: adults + children + elderly == family_size
    for _, row in df1.iterrows():
        assert row["adults_count"] + row["children_count"] + row["elderly_count"] == row["family_size"]
        assert row["family_size"] >= 1


def test_simulate_household_pantry_history():
    """Verify single household simulation over 30 days."""
    household = {
        "household_id": 1,
        "family_size": 4,
        "activity_profile": "MODERATE",
        "dietary_preference": "BALANCED",
    }
    c_records, n_records = simulate_household_pantry_history(household, days=30, seed=123)

    # 4 items * 30 days = 120 records
    assert len(c_records) == 120
    assert len(n_records) == 120

    items_found = set()
    for rec in c_records:
        items_found.add(rec["item_name"])
        assert rec["previous_weight"] >= 0.0
        assert rec["current_weight"] >= 0.0
        assert rec["measured_weight"] >= 0.0
        assert rec["consumption_grams"] >= 0.0
        assert rec["refill_grams"] >= 0.0

    assert items_found == {"Rice", "Sugar", "Salt", "Ghee"}

    # Verify nutrition values are calculated
    for n_rec in n_records:
        assert n_rec["calories_kcal"] >= 0.0
        assert n_rec["carbohydrates_g"] >= 0.0
        assert n_rec["protein_g"] >= 0.0


def test_generator_small_batch_save(tmp_path):
    """Verify dataset generation and saving to disk with small batch."""
    paths = generate_and_save_datasets(num_households=5, days=10, output_dir=tmp_path, seed=99)
    assert paths["households"].exists()
    assert paths["consumption"].exists()
    assert paths["nutrition"].exists()

    df_h = pd.read_csv(paths["households"])
    assert len(df_h) == 5
    df_c = pd.read_csv(paths["consumption"])
    assert len(df_c) == 5 * 10 * 4
