from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.train import TrainType, TrainStatus


class TrainBase(BaseModel):
    train_number: str = Field(..., min_length=1, max_length=10)
    train_name: str = Field(..., min_length=1, max_length=100)
    train_type: TrainType
    origin_station_id: int
    destination_station_id: int
    route_id: int
    total_stops: int = Field(default=0, ge=0)
    total_distance_km: float = Field(default=0.0, ge=0)
    scheduled_departure: datetime
    scheduled_arrival: datetime


class TrainCreate(TrainBase):
    pass


class TrainUpdate(BaseModel):
    train_name: Optional[str] = Field(None, min_length=1, max_length=100)
    train_type: Optional[TrainType] = None
    status: Optional[TrainStatus] = None
    is_active: Optional[bool] = None


class TrainResponse(TrainBase):
    id: int
    status: TrainStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainListResponse(BaseModel):
    trains: List[TrainResponse]
    total: int
    page: int
    page_size: int


class TrainPositionBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed_kmh: float = Field(default=0.0, ge=0)
    heading: Optional[float] = Field(None, ge=0, le=360)
    current_station_id: Optional[int] = None
    next_station_id: Optional[int] = None
    distance_to_next_km: Optional[float] = Field(None, ge=0)
    distance_travelled_km: float = Field(default=0.0, ge=0)
    delay_minutes: int = Field(default=0)
    source: str = Field(default="SIMULATION")


class TrainPositionCreate(TrainPositionBase):
    train_id: int
    timestamp: Optional[datetime] = None


class TrainPositionResponse(TrainPositionBase):
    id: int
    train_id: int
    timestamp: datetime
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


class TrainScheduleResponse(BaseModel):
    id: int
    station_id: int
    station_code: str
    station_name: str
    sequence: int
    scheduled_arrival: Optional[datetime] = None
    scheduled_departure: Optional[datetime] = None
    scheduled_dwell_minutes: int
    distance_from_origin_km: float
    is_origin: bool
    is_destination: bool
    platform: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TrainEventResponse(BaseModel):
    id: int
    train_id: int
    station_id: Optional[int] = None
    event_type: str
    description: str
    delay_minutes: int
    timestamp: datetime
    source: str
    event_metadata: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class TrainLiveResponse(BaseModel):
    train: TrainResponse
    current_position: Optional[TrainPositionResponse] = None
    next_station: Optional[TrainScheduleResponse] = None
    current_speed_kmh: float
    average_speed_kmh: float
    distance_travelled_km: float
    distance_remaining_km: float
    current_delay_minutes: int
    delay_trend: str
    eta_at_destination: Optional[datetime] = None
    prediction_interval_lower: Optional[datetime] = None
    prediction_interval_upper: Optional[datetime] = None
    confidence_score: Optional[float] = None
    data_source: str


class TrainETAPrediction(BaseModel):
    station_id: int
    station_code: str
    station_name: str
    scheduled_arrival: Optional[datetime] = None
    scheduled_departure: Optional[datetime] = None
    predicted_arrival: Optional[datetime] = None
    predicted_departure: Optional[datetime] = None
    arrival_delay_minutes: Optional[float] = None
    departure_delay_minutes: Optional[float] = None
    confidence: Optional[float] = None
    prediction_interval_lower: Optional[datetime] = None
    prediction_interval_upper: Optional[datetime] = None


class TrainRouteResponse(BaseModel):
    train_id: int
    train_number: str
    origin: TrainScheduleResponse
    destination: TrainScheduleResponse
    upcoming_stations: List[TrainScheduleResponse]
    passed_stations: List[TrainScheduleResponse]


class TrainWeatherResponse(BaseModel):
    next_station_weather: Optional["WeatherResponse"] = None
    route_weather: List["WeatherResponse"] = []
    destination_weather: Optional["WeatherResponse"] = None


from backend.app.schemas.weather import WeatherResponse