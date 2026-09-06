"""
Unit tests for calculations.py in Smart Pantry Management System.
Covers:
- Consumption calculation
- Refill detection & separation
- Average daily intake computation
- Availability status logic (AVAILABLE, LOW, UNAVAILABLE)
- Intake threshold evaluation (NORMAL, HIGH, INSUFFICIENT DATA)
- Estimated remaining days calculation
"""

from datetime import datetime, timezone, timedelta
import pytest

from backend.calculations import (
    calculate_availability_status,
    calculate_consumption_intervals,
    calculate_average_daily_intake,
    calculate_intake_status,
    calculate_remaining_days,
)


def test_availability_status_available():
    """Item with current_quantity > minimum_quantity should be AVAILABLE."""
    assert calculate_availability_status(current_quantity=3200, minimum_quantity=1000) == "AVAILABLE"
    assert calculate_availability_status(current_quantity=1001, minimum_quantity=1000) == "AVAILABLE"


def test_availability_status_low():
    """Item with 0 < current_quantity <= minimum_quantity should be LOW."""
    assert calculate_availability_status(current_quantity=1000, minimum_quantity=1000) == "LOW"
    assert calculate_availability_status(current_quantity=700, minimum_quantity=1000) == "LOW"
    assert calculate_availability_status(current_quantity=1, minimum_quantity=1000) == "LOW"


def test_availability_status_unavailable():
    """Item with current_quantity <= 0 should be UNAVAILABLE."""
    assert calculate_availability_status(current_quantity=0, minimum_quantity=1000) == "UNAVAILABLE"
    assert calculate_availability_status(current_quantity=-10, minimum_quantity=1000) == "UNAVAILABLE"


def test_consumption_simple_decrease():
    """Consecutive decrease in weight should be recorded as consumption."""
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)

    readings = [
        {"timestamp": t0, "weight": 5000.0},
        {"timestamp": t1, "weight": 4750.0},
    ]
    intervals = calculate_consumption_intervals(readings)

    assert len(intervals) == 1
    assert intervals[0]["previous_weight"] == 5000.0
    assert intervals[0]["current_weight"] == 4750.0
    assert intervals[0]["consumption"] == 250.0
    assert intervals[0]["refill_amount"] == 0.0


def test_refill_detection_without_false_consumption():
    """
    Test user specification example:
    5000 g -> 4500 g -> 7000 g -> 6800 g
    Should be:
      Step 1: 5000 -> 4500 (consumption: 500, refill: 0)
      Step 2: 4500 -> 7000 (consumption: 0, refill: 2500)
      Step 3: 7000 -> 6800 (consumption: 200, refill: 0)
    Total consumption: 700 g (NOT 4300 g across refill).
    """
    base = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    readings = [
        {"timestamp": base, "weight": 5000.0},
        {"timestamp": base + timedelta(days=1), "weight": 4500.0},
        {"timestamp": base + timedelta(days=2), "weight": 7000.0},
        {"timestamp": base + timedelta(days=3), "weight": 6800.0},
    ]

    intervals = calculate_consumption_intervals(readings)
    assert len(intervals) == 3

    # Step 1
    assert intervals[0]["consumption"] == 500.0
    assert intervals[0]["refill_amount"] == 0.0

    # Step 2 (Refill)
    assert intervals[1]["consumption"] == 0.0
    assert intervals[1]["refill_amount"] == 2500.0

    # Step 3
    assert intervals[2]["consumption"] == 200.0
    assert intervals[2]["refill_amount"] == 0.0

    total_consumption = sum(i["consumption"] for i in intervals)
    total_refill = sum(i["refill_amount"] for i in intervals)

    assert total_consumption == 700.0
    assert total_refill == 2500.0


def test_average_daily_intake_multi_days():
    """Multi-day consumption: total consumption / distinct days with consumption."""
    base = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    readings = [
        {"timestamp": base, "weight": 5000.0},
        {"timestamp": base + timedelta(days=1), "weight": 4750.0},  # 250g on Day 2
        {"timestamp": base + timedelta(days=2), "weight": 4500.0},  # 250g on Day 3
        {"timestamp": base + timedelta(days=3), "weight": 4250.0},  # 250g on Day 4
        {"timestamp": base + timedelta(days=4), "weight": 4000.0},  # 250g on Day 5
    ]

    avg, days = calculate_average_daily_intake(readings)
    assert days == 4
    # Total consumption = 1000g across 4 days = 250g/day
    assert avg == 250.0


def test_average_daily_intake_insufficient_data():
    """Empty or single reading must return None, 0 for insufficient data."""
    assert calculate_average_daily_intake([]) == (None, 0)
    assert calculate_average_daily_intake([{"timestamp": datetime.now(), "weight": 5000.0}]) == (None, 0)

    # Constant weight (no consumption events)
    t = datetime.now()
    readings_no_consumption = [
        {"timestamp": t, "weight": 5000.0},
        {"timestamp": t + timedelta(days=1), "weight": 5000.0}
    ]
    assert calculate_average_daily_intake(readings_no_consumption) == (None, 0)


def test_intake_status():
    """Test normal, high, and insufficient data classifications."""
    threshold = 300.0  # g/day for Rice

    # Insufficient data
    assert calculate_intake_status(average_daily_intake=None, high_intake_threshold=threshold) == "INSUFFICIENT DATA"

    # Normal intake
    assert calculate_intake_status(average_daily_intake=220.0, high_intake_threshold=threshold) == "NORMAL"
    assert calculate_intake_status(average_daily_intake=300.0, high_intake_threshold=threshold) == "NORMAL"

    # High intake
    assert calculate_intake_status(average_daily_intake=350.0, high_intake_threshold=threshold) == "HIGH"


def test_remaining_days_calculation():
    """Test remaining days calculation and edge cases."""
    # 3200g remaining / 220g daily intake ~ 14.5 days
    rem = calculate_remaining_days(current_quantity=3200.0, average_daily_intake=220.0)
    assert rem == 14.5

    # Insufficient data cases
    assert calculate_remaining_days(current_quantity=3200.0, average_daily_intake=None) is None
    assert calculate_remaining_days(current_quantity=0.0, average_daily_intake=220.0) is None
    assert calculate_remaining_days(current_quantity=-5.0, average_daily_intake=220.0) is None
    assert calculate_remaining_days(current_quantity=1000.0, average_daily_intake=0.0) is None
