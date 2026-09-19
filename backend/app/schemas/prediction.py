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