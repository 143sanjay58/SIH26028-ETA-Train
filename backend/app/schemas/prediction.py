from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class PredictionExplanationResponse(BaseModel):
    factor_name: str
    factor_value: float
    contribution_minutes: float
    direction: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class PredictionResponse(BaseModel):
    id: int
    train_id: int
    station_id: int
    model_type: str
    model_version: str
    predicted_arrival_delay_minutes: Optional[float] = None
    predicted_departure_delay_minutes: Optional[float] = None
    predicted_remaining_time_minutes: Optional[float] = None
    predicted_arrival_time: Optional[datetime] = None
    prediction_interval_lower: Optional[float] = None
    prediction_interval_upper: Optional[float] = None
    confidence_score: Optional[float] = None
    features: Optional[Dict] = None
    feature_importance: Optional[Dict] = None
    prediction_time: datetime
    is_current: bool
    latency_ms: Optional[int] = None
    explanations: List[PredictionExplanationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ETARequest(BaseModel):
    train_number: str
    include_explanations: bool = True
    include_uncertainty: bool = True


class ETAResponse(BaseModel):
    train_number: str
    train_name: str
    current_station: Optional[str] = None
    next_station: Optional[str] = None
    destination_station: str
    current_delay_minutes: int
    predicted_arrival_delay_minutes: float
    predicted_arrival_time: datetime
    prediction_interval_lower: Optional[datetime] = None
    prediction_interval_upper: Optional[datetime] = None
    confidence_score: Optional[float] = None
    model_type: str
    model_version: str
    explanations: List[PredictionExplanationResponse] = []
    data_source: str
    generated_at: datetime


class SIHUpcomingStation(BaseModel):
    """One upcoming station served by the SIH26028 ETA core."""

    station_code: str
    station_name: str
    route_position: int
    scheduled_remaining_minutes: float
    predicted_remaining_minutes: float
    predicted_arrival_delay_minutes: float
    predicted_eta: datetime


class SIHETAResponse(BaseModel):
    """Unified ETA response from the embedded SIH26028 (LightGBM) core."""

    train_number: str
    train_name: str
    current_station: str
    current_station_name: Optional[str] = None
    current_route_position: int
    current_delay_minutes: float
    current_time: Optional[str] = None
    destination_station: Optional[str] = None
    destination_station_name: Optional[str] = None
    predicted_arrival_delay_minutes: float
    predicted_arrival_time: str
    predicted_remaining_minutes: float
    upcoming_station_count: int
    upcoming_stations: List[SIHUpcomingStation] = []
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    impact_severity: Optional[str] = None
    delay_trend: Optional[str] = None
    route_impact: Optional[str] = None
    model_type: str = "SIH_ETA_CORE"
    model_version: str = "STAGE13-LGBM"
    data_source: str = "SIH_ETA_CORE"
    position_source: Optional[str] = None
    generated_at: str