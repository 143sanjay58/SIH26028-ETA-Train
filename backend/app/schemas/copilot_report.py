from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from backend.app.models.copilot_report import (
    CoPilotReportReason,
    CoPilotReportPriority,
    CoPilotReportStatus,
)


class CoPilotReportCreate(BaseModel):
    train_number: str = Field(..., min_length=1, max_length=10)
    station_code: Optional[str] = Field(None, max_length=10)
    reason: CoPilotReportReason
    priority: CoPilotReportPriority = CoPilotReportPriority.MEDIUM
    message: str = Field(..., min_length=1, max_length=2000)
    current_delay_minutes: int = Field(0, ge=0, le=1440)


class CoPilotReportResponse(BaseModel):
    id: int
    train_id: Optional[int] = None
    user_id: int
    station_id: Optional[int] = None
    train_number: str
    station_code: Optional[str] = None
    reason: CoPilotReportReason
    priority: CoPilotReportPriority
    message: str
    current_delay_minutes: int
    status: CoPilotReportStatus
    is_active: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    closed_by: Optional[int] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    reporter_call_sign: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)