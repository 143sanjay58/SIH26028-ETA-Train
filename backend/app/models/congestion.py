from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class CongestionLevel(str):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CongestionState(Base):
    __tablename__ = "congestion_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[Optional[int]] = mapped_column(ForeignKey("route_sections.id"), nullable=True, index=True)
    station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True, index=True)
    
    train_count: Mapped[int] = mapped_column(Integer, default=0)
    train_density_per_km: Mapped[float] = mapped_column(Float, default=0.0)
    avg_speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_delay_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    
    preceding_train_delay_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    following_train_delay_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    level: Mapped[str] = mapped_column(String(20), default=CongestionLevel.LOW)
    historical_congestion_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    congestion_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    section: Mapped["RouteSection"] = relationship("RouteSection")
    station: Mapped[Optional["Station"]] = relationship("Station")

    __table_args__ = (
        Index("ix_congestion_section_time", "section_id", "measured_at"),
        Index("ix_congestion_station_time", "station_id", "measured_at"),
    )