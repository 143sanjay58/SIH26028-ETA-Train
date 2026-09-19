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


class TrainType(str, enum.Enum):
    EXPRESS = "EXPRESS"
    SUPERFAST = "SUPERFAST"
    MAIL = "MAIL"
    PASSENGER = "PASSENGER"
    SUBURBAN = "SUBURBAN"
    FREIGHT = "FREIGHT"
    RAJDHANI = "RAJDHANI"
    SHATABDI = "SHATABDI"
    DURONTO = "DURONTO"
    VANDE_BHARAT = "VANDE_BHARAT"


class TrainStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    DELAYED = "DELAYED"
    ARRIVED = "ARRIVED"
    CANCELLED = "CANCELLED"
    DIVERTED = "DIVERTED"
    TERMINATED = "TERMINATED"


class Train(Base):
    __tablename__ = "trains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_number: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    train_name: Mapped[str] = mapped_column(String(100), nullable=False)
    train_type: Mapped[TrainType] = mapped_column(Enum(TrainType), nullable=False)
    origin_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    destination_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False)
    total_stops: Mapped[int] = mapped_column(Integer, default=0)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    scheduled_departure: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_arrival: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[TrainStatus] = mapped_column(Enum(TrainStatus), default=TrainStatus.SCHEDULED)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    origin_station: Mapped["Station"] = relationship("Station", foreign_keys=[origin_station_id])
    destination_station: Mapped["Station"] = relationship("Station", foreign_keys=[destination_station_id])
    route: Mapped["Route"] = relationship("Route", back_populates="trains")
    positions: Mapped[list["TrainPosition"]] = relationship("TrainPosition", back_populates="train", order_by="TrainPosition.timestamp.desc()")
    schedules: Mapped[list["TrainSchedule"]] = relationship("TrainSchedule", back_populates="train", order_by="TrainSchedule.sequence")
    events: Mapped[list["TrainEvent"]] = relationship("TrainEvent", back_populates="train", order_by="TrainEvent.timestamp.desc()")
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="train", order_by="Prediction.created_at.desc()")

    __table_args__ = (
        Index("ix_trains_number_status", "train_number", "status"),
        Index("ix_trains_route_status", "route_id", "status"),
    )


class TrainPosition(Base):
    __tablename__ = "train_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True)
    next_station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True)
    distance_to_next_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_travelled_km: Mapped[float] = mapped_column(Float, default=0.0)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    source: Mapped[str] = mapped_column(String(20), default="SIMULATION")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)

    train: Mapped["Train"] = relationship("Train", back_populates="positions")
    current_station: Mapped[Optional["Station"]] = relationship("Station", foreign_keys=[current_station_id])
    next_station: Mapped[Optional["Station"]] = relationship("Station", foreign_keys=[next_station_id])

    __table_args__ = (
        Index("ix_train_positions_train_time", "train_id", "timestamp"),
        Index("ix_train_positions_station_time", "current_station_id", "timestamp"),
    )


class TrainSchedule(Base):
    __tablename__ = "train_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False, index=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_arrival: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_departure: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_dwell_minutes: Mapped[int] = mapped_column(Integer, default=2)
    distance_from_origin_km: Mapped[float] = mapped_column(Float, default=0.0)
    is_origin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_destination: Mapped[bool] = mapped_column(Boolean, default=False)
    platform: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    train: Mapped["Train"] = relationship("Train", back_populates="schedules")
    station: Mapped["Station"] = relationship("Station")

    __table_args__ = (
        Index("ix_train_schedules_train_seq", "train_id", "sequence"),
        Index("ix_train_schedules_station", "station_id"),
    )


class TrainEvent(Base):
    __tablename__ = "train_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"), nullable=False, index=True)
    station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stations.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    source: Mapped[str] = mapped_column(String(20), default="SYSTEM")
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    train: Mapped["Train"] = relationship("Train", back_populates="events")
    station: Mapped[Optional["Station"]] = relationship("Station")

    __table_args__ = (
        Index("ix_train_events_train_time", "train_id", "timestamp"),
        Index("ix_train_events_type_time", "event_type", "timestamp"),
    )