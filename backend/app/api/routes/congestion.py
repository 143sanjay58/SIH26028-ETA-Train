from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from backend.app.database.session import get_db
from backend.app.services.congestion_service import CongestionService
from backend.app.schemas.congestion import CongestionStateResponse
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User

router = APIRouter(prefix="/api/congestion", tags=["congestion"])


@router.get("/network", response_model=List[CongestionStateResponse])
async def get_network_congestion(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CongestionService(db)
    congestion = await service.get_network_congestion()
    return [CongestionStateResponse.model_validate(c) for c in congestion]


@router.get("/section/{section_id}", response_model=CongestionStateResponse)
async def get_section_congestion(
    section_id: int,
    time_window_minutes: int = Query(10, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CongestionService(db)
    congestion = await service.calculate_section_congestion(section_id, time_window_minutes)
    return CongestionStateResponse.model_validate(congestion)


@router.get("/station/{station_id}", response_model=CongestionStateResponse)
async def get_station_congestion(
    station_id: int,
    time_window_minutes: int = Query(30, ge=1, le=120),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = CongestionService(db)
    congestion = await service.calculate_station_congestion(station_id, time_window_minutes)
    return CongestionStateResponse.model_validate(congestion)