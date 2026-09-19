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
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.session import Base


class WeatherSeverity(str):
    NORMAL = "NORMAL"
    CAUTION = "CAUTION"
    SEVERE = "SEVERE"


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    feels_like_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    pressure_hpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    wind_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    wind_direction_degrees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_gust_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    visibility_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cloud_cover_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    weather_condition: Mapped[str] = mapped_column(String(50), nullable=False)
    weather_description: Mapped[str] = mapped_column(String(200), nullable=False)
    weather_icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    precipitation_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precipitation_probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    severity: Mapped[str] = mapped_column(String(20), default=WeatherSeverity.NORMAL)
    
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), default="OPEN_METEO")
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    station: Mapped["Station"] = relationship("Station")

    __table_args__ = (
        Index("ix_weather_obs_station_time", "station_id", "observed_at"),
        Index("ix_weather_obs_location_time", "latitude", "longitude", "observed_at"),
    )


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False)
    feels_like_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    pressure_hpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    wind_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    wind_direction_degrees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_gust_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    visibility_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cloud_cover_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    weather_condition: Mapped[str] = mapped_column(String(50), nullable=False)
    weather_description: Mapped[str] = mapped_column(String(200), nullable=False)
    weather_icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    precipitation_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precipitation_probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    severity: Mapped[str] = mapped_column(String(20), default=WeatherSeverity.NORMAL)
    
    source: Mapped[str] = mapped_column(String(20), default="OPEN_METEO")
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    station: Mapped["Station"] = relationship("Station")

    __table_args__ = (
        Index("ix_weather_forecast_station_time", "station_id", "forecast_time"),
        Index("ix_weather_forecast_valid", "valid_from", "valid_to"),
    )