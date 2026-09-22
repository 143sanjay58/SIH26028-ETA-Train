from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.station import (
    StationType,
    StationReportStatus,
    StationReportEventType,
    StationSeverity,
)


class StationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    station_type: StationType = StationType.HALT
    zone: Optional[str] = Field(None, max_length=50)
    division: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    platform_count: int = Field(default=1, ge=1)
    is_junction: bool = False


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    station_type: Optional[StationType] = None
    zone: Optional[str] = Field(None, max_length=50)
    division: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    platform_count: Optional[int] = Field(None, ge=1)
    is_junction: Optional[bool] = None
    is_active: Optional[bool] = None


class StationResponse(StationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StationListResponse(BaseModel):
    stations: List[StationResponse]
    total: int
    page: int
    page_size: int


class StationReportBase(BaseModel):
    train_id: int
    station_id: int
    event_type: StationReportEventType
    severity: StationSeverity = StationSeverity.MEDIUM
    description: str = Field(..., min_length=1)
    start_time: datetime
    expected_resolution: Optional[datetime] = None
    delay_impact_minutes: Optional[int] = Field(None, ge=0)
    report_metadata: Optional[dict] = None


class StationReportCreate(StationReportBase):
    pass


class StationReportUpdate(BaseModel):
    event_type: Optional[StationReportEventType] = None
    severity: Optional[StationSeverity] = None
    description: Optional[str] = Field(None, min_length=1)
    expected_resolution: Optional[datetime] = None
    actual_resolution: Optional[datetime] = None
    status: Optional[StationReportStatus] = None
    delay_impact_minutes: Optional[int] = Field(None, ge=0)
    report_metadata: Optional[dict] = None


class StationReportResponse(StationReportBase):
    id: int
    reported_by_user_id: int
    verified_by_user_id: Optional[int] = None
    actual_resolution: Optional[datetime] = None
    status: StationReportStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StationEventResponse(BaseModel):
    id: int
    station_id: int
    train_id: Optional[int] = None
    event_type: str
    description: str
    scheduled_time: Optional[datetime] = None
    actual_time: datetime
    dwell_minutes: Optional[int] = None
    expected_dwell_minutes: Optional[int] = None
    is_extended_halt: bool
    extended_minutes: Optional[int] = None
    source: str
    event_metadata: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)