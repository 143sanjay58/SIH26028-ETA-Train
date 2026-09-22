from datetime import datetime
from typing import Optional, List, TypeVar, Generic
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DataSource(str, Enum):
    LIVE = "LIVE"
    CACHED = "CACHED"
    SIMULATION = "SIMULATION"
    ESTIMATED = "ESTIMATED"
    GPS_DERIVED = "GPS_DERIVED"
    WEATHER_API = "WEATHER_API"


class PaginatedResponse(BaseModel, Generic[TypeVar("T")]):
    items: List[TypeVar("T")]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)