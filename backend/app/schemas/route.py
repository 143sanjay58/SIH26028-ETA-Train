from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class RouteBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RouteResponse(RouteBase):
    id: int
    total_distance_km: float
    total_stations: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteSectionResponse(BaseModel):
    id: int
    route_id: int
    from_station_id: int
    from_station_code: str
    from_station_name: str
    to_station_id: int
    to_station_code: str
    to_station_name: str
    sequence: int
    distance_km: float
    scheduled_travel_time_minutes: int
    max_speed_kmh: int
    is_electrified: bool
    track_type: str
    gradient: Optional[float] = None
    curvature: Optional[float] = None
    historical_avg_time_minutes: Optional[float] = None
    historical_median_time_minutes: Optional[float] = None
    historical_std_dev_minutes: Optional[float] = None
    historical_delay_probability: Optional[float] = None
    historical_recovery_minutes: Optional[float] = None
    sample_count: int

    model_config = ConfigDict(from_attributes=True)