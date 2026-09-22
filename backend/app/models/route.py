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


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    total_stations: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    trains: Mapped[list["Train"]] = relationship("Train", back_populates="route")
    sections: Mapped[list["RouteSection"]] = relationship("RouteSection", back_populates="route", order_by="RouteSection.sequence")

    __table_args__: tuple = ()


class RouteSection(Base):
    __tablename__ = "route_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False, index=True)
    from_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    to_station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    scheduled_travel_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_speed_kmh: Mapped[int] = mapped_column(Integer, default=110)
    is_electrified: Mapped[bool] = mapped_column(Boolean, default=True)
    track_type: Mapped[str] = mapped_column(String(20), default="BROAD_GAUGE")
    gradient: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    curvature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    route: Mapped["Route"] = relationship("Route", back_populates="sections")
    from_station: Mapped["Station"] = relationship("Station", foreign_keys=[from_station_id])
    to_station: Mapped["Station"] = relationship("Station", foreign_keys=[to_station_id])

    # Historical statistics
    historical_avg_time_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    historical_median_time_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    historical_std_dev_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    historical_delay_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    historical_recovery_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_route_sections_route_seq", "route_id", "sequence"),
        Index("ix_route_sections_stations", "from_station_id", "to_station_id"),
    )