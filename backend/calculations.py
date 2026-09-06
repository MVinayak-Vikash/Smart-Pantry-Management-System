"""
Pure business logic and calculation module for the Smart Pantry Management System.
All calculations (consumption, refills, intake averages, availability, and remaining days)
are isolated here for testability and maintainability.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple


def calculate_availability_status(current_quantity: float, minimum_quantity: float) -> str:
    """
    Determine item availability:
    - current_quantity <= 0 -> UNAVAILABLE
    - current_quantity <= minimum_quantity -> LOW
    - otherwise -> AVAILABLE
    """
    if current_quantity <= 0:
        return "UNAVAILABLE"
    if current_quantity <= minimum_quantity:
        return "LOW"
    return "AVAILABLE"


def calculate_consumption_intervals(
    readings: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compute consumption and refill intervals for a chronologically ordered list of readings.
    
    Each reading dict should have:
      - 'weight': float
      - 'timestamp': datetime (or ISO string)
      - 'id': Optional[int]

    Returns a list of dicts:
      - 'timestamp': datetime
      - 'previous_weight': float
      - 'current_weight': float
      - 'consumption': float (>= 0)
      - 'refill_amount': float (>= 0)
    """
    if len(readings) < 2:
        return []

    # Sort chronologically by timestamp
    sorted_readings = sorted(readings, key=lambda r: r["timestamp"])
    intervals = []

    for i in range(1, len(sorted_readings)):
        prev_w = float(sorted_readings[i - 1]["weight"])
        curr_w = float(sorted_readings[i]["weight"])
        curr_time = sorted_readings[i]["timestamp"]

        if curr_w < prev_w:
            # Consumption event
            consumption = round(prev_w - curr_w, 2)
            refill = 0.0
        elif curr_w > prev_w:
            # Refill / replenishment event
            consumption = 0.0
            refill = round(curr_w - prev_w, 2)
        else:
            # No change
            consumption = 0.0
            refill = 0.0

        intervals.append({
            "timestamp": curr_time,
            "previous_weight": prev_w,
            "current_weight": curr_w,
            "consumption": consumption,
            "refill_amount": refill,
        })

    return intervals


def calculate_average_daily_intake(
    readings: List[Dict[str, Any]]
) -> Tuple[Optional[float], int]:
    """
    Calculate average daily consumption:
      total consumption / number of days with consumption data

    Returns (average_daily_intake, number_of_days_with_data):
      - average_daily_intake: float (grams/day) rounded to 2 decimal places, or None if insufficient data.
      - number_of_days_with_data: int count of distinct calendar days where consumption occurred.
    """
    intervals = calculate_consumption_intervals(readings)
    if not intervals:
        return None, 0

    total_consumption = 0.0
    days_with_consumption = set()

    for interval in intervals:
        cons = interval["consumption"]
        if cons > 0:
            total_consumption += cons
            ts = interval["timestamp"]
            if isinstance(ts, str):
                day_val = ts[:10]
            elif isinstance(ts, (datetime, date)):
                day_val = ts.strftime("%Y-%m-%d")
            else:
                day_val = str(ts)
            days_with_consumption.add(day_val)

    num_days = len(days_with_consumption)
    if num_days == 0 or total_consumption <= 0:
        return None, 0

    avg_intake = round(total_consumption / num_days, 2)
    return avg_intake, num_days


def calculate_intake_status(
    average_daily_intake: Optional[float],
    high_intake_threshold: float
) -> str:
    """
    Compare average daily intake against high_intake_threshold:
    - If average_daily_intake is None (insufficient data) -> INSUFFICIENT DATA
    - If average_daily_intake > high_intake_threshold -> HIGH
    - Otherwise -> NORMAL
    """
    if average_daily_intake is None:
        return "INSUFFICIENT DATA"
    if average_daily_intake > high_intake_threshold:
        return "HIGH"
    return "NORMAL"


def calculate_remaining_days(
    current_quantity: float,
    average_daily_intake: Optional[float]
) -> Optional[float]:
    """
    Estimate remaining days of pantry supply:
    If current_quantity > 0 and average_daily_intake > 0:
      remaining_days = round(current_quantity / average_daily_intake, 1)
    Otherwise:
      None (insufficient data)
    """
    if average_daily_intake is None or average_daily_intake <= 0 or current_quantity <= 0:
        return None
    return round(current_quantity / average_daily_intake, 1)
