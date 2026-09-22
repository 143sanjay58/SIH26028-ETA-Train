from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class AlertType(str, Enum):
    DESTINATION_DELAY = "DESTINATION_DELAY"
    HIGH_CONGESTION = "HIGH_CONGESTION"
    EXTENDED_HALT = "EXTENDED_HALT"
    WEATHER_RISK = "WEATHER_RISK"
    SPEED_ANOMALY = "SPEED_ANOMALY"
    DELAY_PROPAGATION = "DELAY_PROPAGATION"
    TRAIN_RECOVERY = "TRAIN_RECOVERY"
    CONNECTION_RISK = "CONNECTION_RISK"
    ROUTE_DEVIATION = "ROUTE_DEVIATION"
    OPERATIONAL_ANOMALY = "OPERATIONAL_ANOMALY"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertResponse(BaseModel):
    id: int
    train_id: Optional[int] = None
    station_id: Optional[int] = None
    section_id: Optional[int] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    predicted_impact_minutes: Optional[int] = None
    confidence: Optional[float] = None
    is_active: bool
    is_acknowledged: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    alert_metadata: Optional[dict] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)