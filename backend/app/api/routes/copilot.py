from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.core.security import get_current_active_user, require_roles
from backend.app.models.user import User, UserRole
from backend.app.models.copilot_report import (
    CoPilotReport,
    CoPilotReportPriority,
    CoPilotReportReason,
    CoPilotReportStatus,
)
from backend.app.schemas.copilot_report import (
    CoPilotReportCreate,
    CoPilotReportResponse,
)
from backend.app.services.copilot_report_service import CoPilotReportService

router = APIRouter(prefix="/api", tags=["copilot"])

_CONTROL_ROOM = (
    UserRole.SUPERVISOR.value,
    UserRole.OPERATOR.value,
    UserRole.ADMIN.value,
)


def _to_response(report: CoPilotReport) -> CoPilotReportResponse:
    return CoPilotReportResponse(
        id=report.id,
        train_id=report.train_id,
        user_id=report.user_id,
        station_id=report.station_id,
        train_number=report.train_number,
        station_code=report.station_code,
        reason=report.reason,
        priority=report.priority,
        message=report.message,
        current_delay_minutes=report.current_delay_minutes,
        status=report.status,
        is_active=report.is_active,
        acknowledged_by=report.acknowledged_by,
        acknowledged_at=report.acknowledged_at,
        closed_by=report.closed_by,
        closed_at=report.closed_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
        reporter_call_sign=report.reported_by.full_name if report.reported_by else None,
    )


@router.post("/copilot/reports", response_model=CoPilotReportResponse, status_code=201)
async def create_report(
    data: CoPilotReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STATION_STAFF.value)),
):
    service = CoPilotReportService(db)
    report = await service.create_report(current_user, data)
    return _to_response(report)


@router.get("/copilot/reports/mine", response_model=List[CoPilotReportResponse])
async def my_reports(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STATION_STAFF.value)),
):
    service = CoPilotReportService(db)
    reports = await service.list_my_reports(current_user, limit=limit)
    return [_to_response(r) for r in reports]


@router.get("/control-room/reports", response_model=List[CoPilotReportResponse])
async def list_reports(
    status: Optional[CoPilotReportStatus] = Query(None),
    reason: Optional[CoPilotReportReason] = Query(None),
    priority: Optional[CoPilotReportPriority] = Query(None),
    train_number: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(*_CONTROL_ROOM)),
):
    service = CoPilotReportService(db)
    reports = await service.list_reports(
        status=status,
        reason=reason,
        priority=priority,
        train_number=train_number,
        limit=limit,
    )
    return [_to_response(r) for r in reports]


@router.post("/control-room/reports/{report_id}/acknowledge", response_model=CoPilotReportResponse)
async def acknowledge_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_CONTROL_ROOM)),
):
    service = CoPilotReportService(db)
    report = await service.acknowledge_report(report_id, current_user)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_response(report)


@router.post("/control-room/reports/{report_id}/close", response_model=CoPilotReportResponse)
async def close_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_CONTROL_ROOM)),
):
    service = CoPilotReportService(db)
    report = await service.close_report(report_id, current_user)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_response(report)