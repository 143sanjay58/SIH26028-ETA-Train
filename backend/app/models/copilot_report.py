import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class CoPilotReportReason(str, enum.Enum):
    """Operational reasons a train co-pilot can report for a delay."""

    SIGNAL_ISSUE = "SIGNAL_ISSUE"
    TRACK_OBSTRUCTION = "TRACK_OBSTRUCTION"
    TECHNICAL_ISSUE = "TECHNICAL_ISSUE"
    OPERATIONAL_ISSUE = "OPERATIONAL_ISSUE"
    PASSENGER_RELATED = "PASSENGER_RELATED"
    WEATHER_RELATED = "WEATHER_RELATED"
    OTHER = "OTHER"


class CoPilotReportPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CoPilotReportStatus(str, enum.Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLOSED = "CLOSED"


class CoPilotReport(Base):
    """Delay report filed by a train co-pilot (STATION_STAFF) for a train.

    Reports are operational awareness ONLY: they are recorded as events,
    surfaced to the control room as alerts, and stored for future model
    retraining. They are deliberately NOT injected into the 21 ML features
    of the SIH26028 pipeline (those are frozen for the prototype).
    """

    __tablename__ = "copilot_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trains.id"), nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True, index=True)

    train_number: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    station_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    reason: Mapped[CoPilotReportReason] = mapped_column(Enum(CoPilotReportReason), nullable=False)
    priority: Mapped[CoPilotReportPriority] = mapped_column(Enum(CoPilotReportPriority), default=CoPilotReportPriority.MEDIUM)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    current_delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[CoPilotReportStatus] = mapped_column(Enum(CoPilotReportStatus), default=CoPilotReportStatus.NEW, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    acknowledged_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    report_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    train: Mapped[Optional["Train"]] = relationship("Train")
    station: Mapped[Optional["Station"]] = relationship("Station")
    reported_by: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    acknowledged_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[acknowledged_by])
    closed_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[closed_by])

    __table_args__ = (
        Index("ix_copilot_reports_train_status", "train_id", "status"),
        Index("ix_copilot_reports_status_time", "status", "created_at"),
        Index("ix_copilot_reports_user_time", "user_id", "created_at"),
    )