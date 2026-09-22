from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timezone

from backend.app.database.session import get_db
from backend.app.services.train_service import TrainService
from backend.app.schemas.train import (
    TrainCreate,
    TrainUpdate,
    TrainResponse,
    TrainListResponse,
    TrainPositionCreate,
    TrainPositionResponse,
    TrainScheduleResponse,
    TrainEventResponse,
    TrainLiveResponse,
    TrainRouteResponse,
)
from backend.app.core.security import get_current_active_user, require_roles
from backend.app.models.user import User, UserRole

router = APIRouter(prefix="/api/trains", tags=["trains"])


@router.get("", response_model=TrainListResponse)
async def list_trains(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    train_type: Optional[str] = None,
    route_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TrainService(db)
    trains, total = await service.get_trains(page, page_size, status, train_type, route_id)
    return TrainListResponse(
        trains=[TrainResponse.model_validate(t) for t in trains],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
async def create_train(
    train_data: TrainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = TrainService(db)
    train = await service.create_train(train_data)
    return TrainResponse.model_validate(train)


@router.get("/{train_id}", response_model=TrainResponse)
async def get_train(
    train_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TrainService(db)
    train = await service.get_train_by_id(train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    return TrainResponse.model_validate(train)


@router.get("/number/{train_number}", response_model=TrainResponse)
async def get_train_by_number(
    train_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TrainService(db)
    train = await service.get_train_by_number(train_number)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    return TrainResponse.model_validate(train)


@router.patch("/{train_id}", response_model=TrainResponse)
async def update_train(
    train_id: int,
    train_data: TrainUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    service = TrainService(db)
    train = await service.update_train(train_id, train_data)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    return TrainResponse.model_validate(train)


@router.delete("/{train_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_train(
    train_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    service = TrainService(db)
    success = await service.delete_train(train_id)
    if not success:
        raise HTTPException(status_code=404, detail="Train not found")


@router.get("/{train_id}/live", response_model=TrainLiveResponse)
async def get_train_live(
    train_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TrainService(db)
    train = await service.get_train_by_id(train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    position = await service.get_latest_position(train_id)
    upcoming = await service.get_upcoming_stations(train_id, limit=1)

    next_station = None
    if upcoming:
        sched = upcoming[0]
        station = sched.station
        next_station = TrainScheduleResponse(
            id=sched.id,
            station_id=sched.station_id,
            station_code=station.code if station else "",
            station_name=station.name if station else "",
            sequence=sched.sequence,
            scheduled_arrival=sched.scheduled_arrival,
            scheduled_departure=sched.scheduled_departure,
            scheduled_dwell_minutes=sched.scheduled_dwell_minutes,
            distance_from_origin_km=sched.distance_from_origin_km,
            is_origin=sched.is_origin,
            is_destination=sched.is_destination,
            platform=sched.platform,
        )

    current_speed = position.speed_kmh if position else 0
    avg_speed = 60.0
    distance_travelled = position.distance_travelled_km if position else 0
    distance_remaining = train.total_distance_km - distance_travelled
    current_delay = position.delay_minutes if position else 0

    return TrainLiveResponse(
        train=TrainResponse.model_validate(train),
        current_position=TrainPositionResponse.model_validate(position) if position else None,
        next_station=next_station,
        current_speed_kmh=current_speed,
        average_speed_kmh=avg_speed,
        distance_travelled_km=distance_travelled,
        distance_remaining_km=distance_remaining,
        current_delay_minutes=current_delay,
        delay_trend="STABLE",
        data_source=position.source if position else "SIMULATION",
    )


@router.get("/{train_id}/route", response_model=TrainRouteResponse)
async def get_train_route(
    train_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TrainService(db)
    train = await service.get_train_by_id(train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    schedule = await service.get_schedule(train_id)
    position = await service.get_latest_position(train_id)

    current_seq = 0
    if position and position.current_station_id:
        for i, s in enumerate(schedule):
            if s.station_id == position.current_station_id:
                current_seq = i
                break

    def to_schedule_response(s):
        station = s.station
        return TrainScheduleResponse(
            id=s.id,
            station_id=s.station_id,
            station_code=station.code if station else "",
            station_name=station.name if station else "",
            sequence=s.sequence,
            scheduled_arrival=s.scheduled_arrival,
            scheduled_departure=s.scheduled_departure,
            scheduled_dwell_minutes=s.scheduled_dwell_minutes,
            distance_from_origin_km=s.distance_from_origin_km,
            is_origin=s.is_origin,
            is_destination=s.is_destination,
            platform=s.platform,
        )

    upcoming = [to_schedule_response(s) for s in schedule[current_seq + 1:current_seq + 6]]
    passed = [to_schedule_response(s) for s in schedule[:current_seq + 1]]

    origin = to_schedule_response(schedule[0]) if schedule else None
    destination = to_schedule_response(schedule[-1]) if schedule else None

    return TrainRouteResponse(
        train_id=train.id,
        train_number=train.train_number,
        origin=origin,
        destination=destination,
        upcoming_stations=upcoming,
        passed_stations=passed,
    )


@router.get("/{train_id}/positions", response_model=List[TrainPositionResponse])
async def get_train_positions(
    train_id: int,
    limit: int = Query(100, ge=1, le=1000),
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TrainService(db)
    positions = await service.get_positions(train_id, limit, since)
    return [TrainPositionResponse.model_validate(p) for p in positions]


@router.post("/{train_id}/positions", response_model=TrainPositionResponse, status_code=status.HTTP_201_CREATED)
async def add_train_position(
    train_id: int,
    position_data: TrainPositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    if position_data.train_id != train_id:
        raise HTTPException(status_code=400, detail="Train ID mismatch")

    service = TrainService(db)
    position = await service.add_position(position_data)
    return TrainPositionResponse.model_validate(position)


@router.get("/{train_id}/events", response_model=List[TrainEventResponse])
async def get_train_events(
    train_id: int,
    limit: int = Query(50, ge=1, le=200),
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = TrainService(db)
    events = await service.get_events(train_id, limit, since)
    return [TrainEventResponse.model_validate(e) for e in events]