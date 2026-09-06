from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


def utc_now():
    """Return current UTC datetime (timezone-aware converted to naive or standard UTC)."""
    return datetime.now(timezone.utc)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    unit = Column(String, default="g", nullable=False)
    initial_quantity = Column(Float, nullable=False)
    current_quantity = Column(Float, nullable=False)
    minimum_quantity = Column(Float, nullable=False)
    high_intake_threshold = Column(Float, nullable=False)
    
    # Flexible field reserved for future RFID container integration
    rfid_uid = Column(String, nullable=True, unique=True, index=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationship to weight readings
    readings = relationship(
        "WeightReading",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="WeightReading.timestamp"
    )

    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', current_quantity={self.current_quantity} {self.unit})>"


class WeightReading(Base):
    __tablename__ = "weight_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    weight = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    # Relationship back to Item
    item = relationship("Item", back_populates="readings")

    def __repr__(self):
        return f"<WeightReading(id={self.id}, item_id={self.item_id}, weight={self.weight}, timestamp={self.timestamp})>"
