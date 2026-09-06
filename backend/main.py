from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend import database, models, schemas, crud, calculations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to initialize tables and default data."""
    database.init_db()
    yield


app = FastAPI(
    title="Smart Pantry Management System API",
    description=(
        "Phase 1 REST API for pantry weight tracking, consumption calculation, "
        "refill detection, and availability/intake classification. "
        "Designed to accept future IoT ESP32 load-cell telemetry and container RFID tags."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local dashboards and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "ok", "service": "Smart Pantry Management System - Phase 1"}


@app.post("/seed", tags=["System"])
def seed_sample_data(db: Session = Depends(database.get_db)):
    """
    Seed realistic multi-day sample sensor readings for Rice, Sugar, Salt, and Ghee.
    Useful for demonstration and automated testing.
    """
    result = crud.seed_sample_readings(db)
    return result


@app.get("/items", response_model=List[schemas.ItemSummaryResponse], tags=["Items"])
def get_all_items(db: Session = Depends(database.get_db)):
    """
    Get all pantry items with their current quantity, availability status,
    average daily intake, and intake warning status.
    """
    items = crud.get_items(db)
    results = []
    for item in items:
        metrics = crud.compute_item_metrics(item)
        results.append(schemas.ItemSummaryResponse(**metrics))
    return results


@app.get("/items/{item_id}", response_model=schemas.ItemDetailResponse, tags=["Items"])
def get_item_detail(item_id: int, db: Session = Depends(database.get_db)):
    """
    Get detailed profile of a specific item, including thresholds,
    calculated availability/intake status, and historical weight readings.
    """
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found."
        )

    metrics = crud.compute_item_metrics(item)
    readings = [
        schemas.WeightReadingResponse(
            id=r.id,
            item_id=r.item_id,
            weight=r.weight,
            timestamp=r.timestamp
        )
        for r in item.readings
    ]

    return schemas.ItemDetailResponse(
        **metrics,
        recent_weight_history=readings
    )


@app.post("/items/{item_id}/weight", tags=["Weight Ingestion"])
def add_weight_reading(
    item_id: int,
    payload: schemas.WeightReadingCreate,
    db: Session = Depends(database.get_db)
):
    """
    Record a new weight reading (simulated or from future ESP32/HX711 load cell).
    Updates item current_quantity, logs reading, and returns updated status.
    """
    item = crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found."
        )

    reading = crud.create_weight_reading(db, item_id=item_id, weight=payload.weight)
    metrics = crud.compute_item_metrics(item)

    return {
        "message": "Weight reading recorded successfully",
        "reading": {
            "id": reading.id,
            "item_id": reading.item_id,
            "weight": reading.weight,
            "timestamp": reading.timestamp,
        },
        "item_status": metrics,
    }


@app.get(
    "/items/{item_id}/consumption",
    response_model=schemas.ConsumptionHistoryResponse,
    tags=["Consumption"]
)
def get_consumption_history(item_id: int, db: Session = Depends(database.get_db)):
    """
    Retrieve historical consumption events and refill amounts.
    Weight decreases are counted as consumption; weight increases are treated as refills.
    """
    history = crud.get_item_consumption_history(db, item_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found."
        )
    return schemas.ConsumptionHistoryResponse(**history)


@app.get("/dashboard", response_model=schemas.DashboardSummaryResponse, tags=["Dashboard"])
def get_dashboard_summary(db: Session = Depends(database.get_db)):
    """
    Get aggregated dashboard summary covering all four pantry items,
    stock alerts, and intake warnings.
    """
    items = crud.get_items(db)
    items_summary = []
    available_count = 0
    low_count = 0
    unavailable_count = 0
    high_intake_count = 0

    for item in items:
        metrics = crud.compute_item_metrics(item)
        summary = schemas.ItemSummaryResponse(**metrics)
        items_summary.append(summary)

        if summary.availability_status == "AVAILABLE":
            available_count += 1
        elif summary.availability_status == "LOW":
            low_count += 1
        elif summary.availability_status == "UNAVAILABLE":
            unavailable_count += 1

        if summary.intake_status == "HIGH":
            high_intake_count += 1

    return schemas.DashboardSummaryResponse(
        items=items_summary,
        total_items=len(items_summary),
        available_count=available_count,
        low_count=low_count,
        unavailable_count=unavailable_count,
        high_intake_count=high_intake_count,
    )
