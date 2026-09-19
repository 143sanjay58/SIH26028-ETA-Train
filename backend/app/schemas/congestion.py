from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class CongestionLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CongestionStateResponse(BaseModel):
    id: int
    section_id: Optional[int] = None
    station_id: Optional[int] = None
    train_count: int
    train_density_per_km: float
    avg_speed_kmh: Optional[float] = None
    avg_delay_minutes: float
    preceding_train_delay_minutes: Optional[float] = None
    following_train_delay_minutes: Optional[float] = None
    level: CongestionLevel
    historical_congestion_score: Optional[float] = None
    measured_at: datetime

    model_config = ConfigDict(from_attributes=True)