import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Float,
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


class StationType(str, enum.Enum):
    JUNCTION = "JUNCTION"
    TERMINAL = "TERMINAL"
    HALT = "HALT"
    CROSSING = "CROSSING"
    BLOCK = "BLOCK"


class StationReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class StationReportEventType(str, enum.Enum):
    SIGNAL_WAIT = "SIGNAL_WAIT"
    PLATFORM_OCCUPIED = "PLATFORM_OCCUPIED"
    PRECEDING_TRAIN = "PRECEDING_TRAIN"
    CROSSING_TRAIN = "CROSSING_TRAIN"
    CREW_CHANGE = "CREW_CHANGE"
    TECHNICAL_CHECK = "TECHNICAL_CHECK"
    PASSENGER_ASSISTANCE = "PASSENGER_ASSISTANCE"
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"
    TRACK_WORK = "TRACK_WORK"
    MAINTENANCE_BLOCK = "MAINTENANCE_BLOCK"
    LOCOMOTIVE_ISSUE = "LOCOMOTIVE_ISSUE"
    COACH_ISSUE = "COACH_ISSUE"
    WATER_CLEANING = "WATER_CLEANING"
    WEATHER = "WEATHER"
    SECURITY_CHECK = "SECURITY_CHECK"
    OPERATIONAL_HOLD = "OPERATIONAL_HOLD"
    OTHER = "OTHER"


class StationSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    station_type: Mapped[StationType] = mapped_column(Enum(StationType), default=StationType.HALT)
    zone: Mapped[str] = mapped_column(String(50), nullable=True)
    division: Mapped[str] = mapped_column(String(50), nullable=True)
    state: Mapped[str] = mapped_column(String(50), nullable=True)
    platform_count: Mapped[int] = mapped_column(Integer, default=1)
    is_junction: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    reports: Mapped[list["StationReport"]] = relationship("StationReport", back_populates="station")
    events: Mapped[list["StationEvent"]] = relationship("StationEvent", back_populates="station")

    __table_args__ = (
        Index("ix_stations_code_name", "code", "name"),
        Index("ix_stations_location", "latitude", "longitude"),
    )


class StationReport(Base):
    __tablename__ = "station_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False, index=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False, index=True)
    reported_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    verified_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[StationReportEventType] = mapped_column(Enum(StationReportEventType), nullable=False)
    severity: Mapped[StationSeverity] = mapped_column(Enum(StationSeverity), default=StationSeverity.MEDIUM)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_resolution: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_resolution: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[StationReportStatus] = mapped_column(Enum(StationReportStatus), default=StationReportStatus.PENDING, index=True)
    delay_impact_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    report_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    train: Mapped["Train"] = relationship("Train")
    station: Mapped["Station"] = relationship("Station", back_populates="reports")
    reported_by: Mapped["User"] = relationship("User", foreign_keys=[reported_by_user_id])
    verified_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by_user_id])

    __table_args__ = (
        Index("ix_station_reports_train_station", "train_id", "station_id"),
        Index("ix_station_reports_status_time", "status", "created_at"),
    )


class StationEvent(Base):
    __tablename__ = "station_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False, index=True)
    train_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trains.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    dwell_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_dwell_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_extended_halt: Mapped[bool] = mapped_column(Boolean, default=False)
    extended_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="SYSTEM")
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    station: Mapped["Station"] = relationship("Station", back_populates="events")
    train: Mapped[Optional["Train"]] = relationship("Train")

    __table_args__ = (
        Index("ix_station_events_station_time", "station_id", "actual_time"),
        Index("ix_station_events_train_time", "train_id", "actual_time"),
    )