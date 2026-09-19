from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from backend.app.database.session import get_db
from backend.app.services.weather_service import WeatherService
from backend.app.schemas.weather import WeatherResponse, WeatherObservationResponse, WeatherForecastResponse
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/station/{station_id}", response_model=WeatherResponse)
async def get_station_weather(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = WeatherService(db)
    from backend.app.models.station import Station
    station = await db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    current = await service.get_station_weather(station)
    forecast = await service.get_forecast(station.latitude, station.longitude, station_id, days=3)

    return WeatherResponse(
        station_id=station.id,
        station_code=station.code,
        station_name=station.name,
        latitude=station.latitude,
        longitude=station.longitude,
        current=WeatherObservationResponse.model_validate(current) if current else None,
        forecast=[WeatherForecastResponse.model_validate(f) for f in forecast],
        data_source=current.source if current else "UNAVAILABLE",
        last_updated=current.observed_at if current else datetime.now(timezone.utc),
    )


@router.get("/coordinates", response_model=WeatherResponse)
async def get_weather_by_coordinates(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = WeatherService(db)
    current = await service.get_current_weather(lat, lon)
    forecast = await service.get_forecast(lat, lon, days=3)

    return WeatherResponse(
        station_id=0,
        station_code="GPS",
        station_name=f"GPS Location ({lat:.4f}, {lon:.4f})",
        latitude=lat,
        longitude=lon,
        current=WeatherObservationResponse.model_validate(current) if current else None,
        forecast=[WeatherForecastResponse.model_validate(f) for f in forecast],
        data_source=current.source if current else "UNAVAILABLE",
        last_updated=current.observed_at if current else datetime.now(timezone.utc),
    )


@router.get("/route/{train_id}", response_model=List[WeatherResponse])
async def get_route_weather(
    train_id: int,
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from backend.app.models.train import Train, TrainPosition
    from sqlalchemy import select

    train = await db.get(Train, train_id)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")

    service = WeatherService(db)

    position_result = await db.execute(
        select(TrainPosition)
        .where(TrainPosition.train_id == train_id)
        .order_by(TrainPosition.timestamp.desc())
        .limit(1)
    )
    position = position_result.scalar_one_or_none()

    upcoming_stations = []
    if position and position.current_station_id:
        from backend.app.models.train import TrainSchedule
        schedule_result = await db.execute(
            select(TrainSchedule)
            .where(
                TrainSchedule.train_id == train_id,
                TrainSchedule.sequence > 0,
            )
            .order_by(TrainSchedule.sequence)
            .limit(limit)
        )
        schedules = list(schedule_result.scalars().all())
        for s in schedules:
            station = await db.get(Station, s.station_id)
            if station:
                upcoming_stations.append(station)

    if not upcoming_stations:
        dest_station = await db.get(Station, train.destination_station_id)
        if dest_station:
            upcoming_stations.append(dest_station)

    results = []
    for station in upcoming_stations[:limit]:
        current = await service.get_station_weather(station)
        forecast = await service.get_forecast(station.latitude, station.longitude, station.id, days=1)
        results.append(WeatherResponse(
            station_id=station.id,
            station_code=station.code,
            station_name=station.name,
            latitude=station.latitude,
            longitude=station.longitude,
            current=WeatherObservationResponse.model_validate(current) if current else None,
            forecast=[WeatherForecastResponse.model_validate(f) for f in forecast[:24]],
            data_source=current.source if current else "UNAVAILABLE",
            last_updated=current.observed_at if current else datetime.now(timezone.utc),
        ))

    return results


from datetime import datetime, timezone
from backend.app.models.station import Station