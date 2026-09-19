from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timezone

from backend.app.database.session import get_db
from backend.app.services.station_service import StationService
from backend.app.schemas.station import (
    StationCreate,
    StationUpdate,
    StationResponse,
    StationListResponse,
    StationReportCreate,
    StationReportUpdate,
    StationReportResponse,
    StationEventResponse,
)
from backend.app.schemas.common import PaginatedResponse
from backend.app.core.security import get_current_active_user, require_roles
from backend.app.models.user import User, UserRole
from backend.app.models.station import StationReportStatus

router = APIRouter(prefix="/api/stations", tags=["stations"])


@router.get("", response_model=StationListResponse)
async def list_stations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    station_type: Optional[str] = None,
    state: Optional[str] = None,
    zone: Optional[str] = None,
    is_junction: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = StationService(db)
    stations, total = await service.get_stations(page, page_size, station_type, state, zone, is_junction)
    return StationListResponse(
        stations=[StationResponse.model_validate(s) for s in stations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    station_data: StationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = StationService(db)
    station = await service.create_station(station_data)
    return StationResponse.model_validate(station)


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = StationService(db)
    station = await service.get_station_by_id(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return StationResponse.model_validate(station)


@router.get("/code/{code}", response_model=StationResponse)
async def get_station_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = StationService(db)
    station = await service.get_station_by_code(code)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return StationResponse.model_validate(station)


@router.patch("/{station_id}", response_model=StationResponse)
async def update_station(
    station_id: int,
    station_data: StationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = StationService(db)
    station = await service.update_station(station_id, station_data)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return StationResponse.model_validate(station)


@router.get("/{station_id}/reports", response_model=PaginatedResponse[StationReportResponse])
async def get_station_reports(
    station_id: int,
    train_id: Optional[int] = None,
    status: Optional[StationReportStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = StationService(db)
    reports, total = await service.get_station_reports(station_id, train_id, status, page, page_size)
    return PaginatedResponse(
        items=[StationReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/{station_id}/reports", response_model=StationReportResponse, status_code=status.HTTP_201_CREATED)
async def create_station_report(
    station_id: int,
    report_data: StationReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STATION_STAFF, UserRole.SUPERVISOR, UserRole.OPERATOR, UserRole.ADMIN)),
):
    if report_data.station_id != station_id:
        raise HTTPException(status_code=400, detail="Station ID mismatch")

    service = StationService(db)
    report = await service.create_station_report(report_data, current_user.id)
    return StationReportResponse.model_validate(report)


@router.patch("/reports/{report_id}", response_model=StationReportResponse)
async def update_station_report(
    report_id: int,
    report_data: StationReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STATION_STAFF, UserRole.SUPERVISOR, UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = StationService(db)
    report = await service.update_station_report(report_id, report_data, current_user.id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return StationReportResponse.model_validate(report)


@router.get("/{station_id}/events", response_model=List[StationEventResponse])
async def get_station_events(
    station_id: int,
    train_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = StationService(db)
    events = await service.get_station_events(station_id, train_id, limit, since)
    return [StationEventResponse.model_validate(e) for e in events]