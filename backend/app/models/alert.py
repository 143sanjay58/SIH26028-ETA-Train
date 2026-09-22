from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class AlertType(str):
    DESTINATION_DELAY = "DESTINATION_DELAY"
    HIGH_CONGESTION = "HIGH_CONGESTION"
    EXTENDED_HALT = "EXTENDED_HALT"
    WEATHER_RISK = "WEATHER_RISK"
    SPEED_ANOMALY = "SPEED_ANOMALY"
    DELAY_PROPAGATION = "DELAY_PROPAGATION"
    TRAIN_RECOVERY = "TRAIN_RECOVERY"
    CONNECTION_RISK = "CONNECTION_RISK"
    ROUTE_DEVIATION = "ROUTE_DEVIATION"
    OPERATIONAL_ANOMALY = "OPERATIONAL_ANOMALY"


class AlertSeverity(str):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trains.id"), nullable=True, index=True)
    station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True, index=True)
    section_id: Mapped[Optional[int]] = mapped_column(ForeignKey("route_sections.id"), nullable=True)
    
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default=AlertSeverity.WARNING, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    predicted_impact_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    alert_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    train: Mapped[Optional["Train"]] = relationship("Train")
    station: Mapped[Optional["Station"]] = relationship("Station")
    section: Mapped[Optional["RouteSection"]] = relationship("RouteSection")

    __table_args__ = (
        Index("ix_alerts_train_active", "train_id", "is_active"),
        Index("ix_alerts_type_active", "alert_type", "is_active"),
        Index("ix_alerts_created", "created_at"),
    )