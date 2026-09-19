from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class WeatherBase(BaseModel):
    temperature_celsius: float
    feels_like_celsius: Optional[float] = None
    humidity_percent: int = Field(..., ge=0, le=100)
    pressure_hpa: Optional[float] = None
    wind_speed_kmh: float = Field(..., ge=0)
    wind_direction_degrees: Optional[int] = Field(None, ge=0, le=360)
    wind_gust_kmh: Optional[float] = Field(None, ge=0)
    visibility_km: Optional[float] = Field(None, ge=0)
    cloud_cover_percent: Optional[int] = Field(None, ge=0, le=100)
    weather_condition: str
    weather_description: str
    weather_icon: Optional[str] = None
    precipitation_mm: Optional[float] = Field(None, ge=0)
    precipitation_probability: Optional[int] = Field(None, ge=0, le=100)
    severity: str = "NORMAL"


class WeatherObservationResponse(WeatherBase):
    id: Optional[int] = None
    station_id: Optional[int] = None
    latitude: float
    longitude: float
    observed_at: datetime
    source: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WeatherForecastResponse(WeatherBase):
    id: Optional[int] = None
    station_id: Optional[int] = None
    latitude: float
    longitude: float
    forecast_time: datetime
    valid_from: datetime
    valid_to: datetime
    source: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WeatherResponse(BaseModel):
    station_id: int
    station_code: str
    station_name: str
    latitude: float
    longitude: float
    current: Optional[WeatherObservationResponse] = None
    forecast: List[WeatherForecastResponse] = []
    data_source: str
    last_updated: datetime