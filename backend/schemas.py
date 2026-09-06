from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class WeightReadingCreate(BaseModel):
    weight: float = Field(..., ge=0, description="Weight in grams, must be non-negative")


class WeightReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    weight: float
    timestamp: datetime


class ConsumptionRecord(BaseModel):
    timestamp: datetime
    previous_weight: float
    current_weight: float
    consumption: float
    refill_amount: float


class ItemSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit: str
    current_quantity: float
    minimum_quantity: float
    availability_status: str
    average_daily_intake: Optional[float] = None
    high_intake_threshold: float
    intake_status: str
    remaining_days: Optional[float] = None


class ItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    unit: str
    initial_quantity: float
    current_quantity: float
    minimum_quantity: float
    availability_status: str
    average_daily_intake: Optional[float] = None
    high_intake_threshold: float
    intake_status: str
    remaining_days: Optional[float] = None
    rfid_uid: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    recent_weight_history: List[WeightReadingResponse] = []


class ConsumptionHistoryResponse(BaseModel):
    item_id: int
    item_name: str
    unit: str
    records: List[ConsumptionRecord]
    total_consumption: float
    total_refill: float
    days_with_data: int
    average_daily_intake: Optional[float] = None


class DashboardSummaryResponse(BaseModel):
    items: List[ItemSummaryResponse]
    total_items: int
    available_count: int
    low_count: int
    unavailable_count: int
    high_intake_count: int
