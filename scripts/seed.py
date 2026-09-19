#!/usr/bin/env python3
"""
Seed script for RAILPULSE AI (Railway Intelligence Platform)
Populates database with sample Indian railway data
"""
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import AsyncSessionLocal, init_db
from backend.app.models.train import Train, TrainSchedule, TrainStatus, TrainType
from backend.app.models.station import Station, StationType
from backend.app.models.route import Route, RouteSection
from backend.app.models.user import User, UserRole
from backend.app.core.security import get_password_hash
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


async def seed_stations(db: AsyncSession) -> list[Station]:
    """Create major Indian railway stations"""
    stations_data = [
        {"code": "NDLS", "name": "New Delhi", "lat": 28.6401, "lon": 77.2153, "type": StationType.TERMINAL, "zone": "NR", "division": "Delhi", "state": "Delhi", "platforms": 16, "junction": True},
        {"code": "HWH", "name": "Howrah", "lat": 22.5815, "lon": 88.3426, "type": StationType.TERMINAL, "zone": "ER", "division": "Howrah", "state": "West Bengal", "platforms": 23, "junction": True},
        {"code": "CSTM", "name": "Chhatrapati Shivaji Maharaj Terminus", "lat": 18.9398, "lon": 72.8355, "type": StationType.TERMINAL, "zone": "CR", "division": "Mumbai", "state": "Maharashtra", "platforms": 18, "junction": True},
        {"code": "MAS", "name": "Chennai Central", "lat": 13.0825, "lon": 80.2750, "type": StationType.TERMINAL, "zone": "SR", "division": "Chennai", "state": "Tamil Nadu", "platforms": 17, "junction": True},
        {"code": "SBC", "name": "Krantivira Sangolli Rayanna (Bengaluru)", "lat": 12.9766, "lon": 77.5713, "type": StationType.TERMINAL, "zone": "SWR", "division": "Bengaluru", "state": "Karnataka", "platforms": 10, "junction": True},
        {"code": "HYB", "name": "Hyderabad Deccan", "lat": 17.4239, "lon": 78.4738, "type": StationType.TERMINAL, "zone": "SCR", "division": "Hyderabad", "state": "Telangana", "platforms": 6, "junction": True},
        {"code": "PNBE", "name": "Patna Junction", "lat": 25.6075, "lon": 85.1364, "type": StationType.JUNCTION, "zone": "ECR", "division": "Danapur", "state": "Bihar", "platforms": 10, "junction": True},
        {"code": "ALD", "name": "Prayagraj Junction", "lat": 25.4432, "lon": 81.8256, "type": StationType.JUNCTION, "zone": "NCR", "division": "Prayagraj", "state": "Uttar Pradesh", "platforms": 10, "junction": True},
        {"code": "BPL", "name": "Bhopal Junction", "lat": 23.2615, "lon": 77.4050, "type": StationType.JUNCTION, "zone": "WCR", "division": "Bhopal", "state": "Madhya Pradesh", "platforms": 6, "junction": True},
        {"code": "NGP", "name": "Nagpur Junction", "lat": 21.1466, "lon": 79.0882, "type": StationType.JUNCTION, "zone": "SECR", "division": "Nagpur", "state": "Maharashtra", "platforms": 8, "junction": True},
        {"code": "BZA", "name": "Vijayawada Junction", "lat": 16.5115, "lon": 80.6284, "type": StationType.JUNCTION, "zone": "SCR", "division": "Vijayawada", "state": "Andhra Pradesh", "platforms": 10, "junction": True},
        {"code": "KYN", "name": "Kalyan Junction", "lat": 19.2382, "lon": 73.1305, "type": StationType.JUNCTION, "zone": "CR", "division": "Mumbai", "state": "Maharashtra", "platforms": 8, "junction": True},
        {"code": "LDH", "name": "Ludhiana Junction", "lat": 30.9086, "lon": 75.8573, "type": StationType.JUNCTION, "zone": "NR", "division": "Firozpur", "state": "Punjab", "platforms": 7, "junction": True},
        {"code": "JAT", "name": "Jammu Tawi", "lat": 32.7186, "lon": 74.8581, "type": StationType.TERMINAL, "zone": "NR", "division": "Firozpur", "state": "Jammu & Kashmir", "platforms": 3, "junction": False},
        {"code": "ERS", "name": "Ernakulam Junction", "lat": 9.9816, "lon": 76.2895, "type": StationType.JUNCTION, "zone": "SR", "division": "Thiruvananthapuram", "state": "Kerala", "platforms": 6, "junction": True},
    ]

    stations = []
    for i, data in enumerate(stations_data):
        station = Station(
            id=i + 1,
            code=data["code"],
            name=data["name"],
            latitude=data["lat"],
            longitude=data["lon"],
            station_type=data["type"],
            zone=data["zone"],
            division=data["division"],
            state=data["state"],
            platform_count=data["platforms"],
            is_junction=data["junction"],
            is_active=True,
        )
        stations.append(station)
        db.add(station)

    await db.flush()
    logger.info("Stations seeded", count=len(stations))
    return stations


async def seed_routes(db: AsyncSession, stations: list[Station]) -> list[Route]:
    """Create major railway routes"""
    station_map = {s.code: s for s in stations}

    routes_data = [
        {
            "code": "NDLS-HWH",
            "name": "New Delhi - Howrah Main Line",
            "stations": ["NDLS", "ALD", "PNBE", "HWH"],
            "distances": [0, 636, 1000, 1445],
        },
        {
            "code": "NDLS-CSTM",
            "name": "New Delhi - Mumbai Central Line",
            "stations": ["NDLS", "BPL", "NGP", "KYN", "CSTM"],
            "distances": [0, 707, 1100, 1380, 1384],
        },
        {
            "code": "NDLS-MAS",
            "name": "New Delhi - Chennai Central Line",
            "stations": ["NDLS", "BPL", "NGP", "BZA", "MAS"],
            "distances": [0, 707, 1100, 1500, 2180],
        },
        {
            "code": "NDLS-SBC",
            "name": "New Delhi - Bengaluru Line",
            "stations": ["NDLS", "BPL", "NGP", "BZA", "SBC"],
            "distances": [0, 707, 1100, 1500, 2300],
        },
        {
            "code": "HWH-MAS",
            "name": "Howrah - Chennai Main Line",
            "stations": ["HWH", "BZA", "MAS"],
            "distances": [0, 1100, 1650],
        },
        {
            "code": "CSTM-HWH",
            "name": "Mumbai - Howrah via Nagpur",
            "stations": ["CSTM", "KYN", "NGP", "BZA", "HWH"],
            "distances": [0, 50, 1000, 1400, 1900],
        },
    ]

    routes = []
    for i, data in enumerate(routes_data):
        route_stations = [station_map[code] for code in data["stations"] if code in station_map]
        if len(route_stations) < 2:
            continue

        route = Route(
            id=i + 1,
            code=data["code"],
            name=data["name"],
            total_distance_km=data["distances"][-1],
            total_stations=len(route_stations),
            is_active=True,
        )
        routes.append(route)
        db.add(route)
        await db.flush()

        for j in range(len(route_stations) - 1):
            from_station = route_stations[j]
            to_station = route_stations[j + 1]
            distance = data["distances"][j + 1] - data["distances"][j]
            scheduled_time = int(distance / 60 * 60)

            section = RouteSection(
                route_id=route.id,
                from_station_id=from_station.id,
                to_station_id=to_station.id,
                sequence=j + 1,
                distance_km=distance,
                scheduled_travel_time_minutes=scheduled_time,
                max_speed_kmh=110 if "RAJDHANI" in data["name"] or "SHATABDI" in data["name"] else 100,
                historical_avg_time_minutes=scheduled_time * 1.1,
                historical_median_time_minutes=scheduled_time,
                historical_std_dev_minutes=scheduled_time * 0.15,
                historical_delay_probability=0.3,
                historical_recovery_minutes=5.0,
                sample_count=100,
            )
            db.add(section)

    await db.flush()
    logger.info("Routes seeded", count=len(routes))
    return routes


async def seed_trains(db: AsyncSession, stations: list[Station], routes: list[Route]) -> list[Train]:
    """Create sample trains"""
    station_map = {s.code: s for s in stations}
    route_map = {r.code: r for r in routes}

    trains_data = [
        {
            "number": "12301",
            "name": "Rajdhani Express",
            "type": TrainType.RAJDHANI,
            "origin": "NDLS",
            "destination": "HWH",
            "route": "NDLS-HWH",
            "stops": ["NDLS", "ALD", "PNBE", "HWH"],
            "departure": "16:55",
            "arrival": "10:05+1",
        },
        {
            "number": "12302",
            "name": "Rajdhani Express",
            "type": TrainType.RAJDHANI,
            "origin": "HWH",
            "destination": "NDLS",
            "route": "NDLS-HWH",
            "stops": ["HWH", "PNBE", "ALD", "NDLS"],
            "departure": "16:55",
            "arrival": "10:05+1",
        },
        {
            "number": "12951",
            "name": "Mumbai Rajdhani",
            "type": TrainType.RAJDHANI,
            "origin": "NDLS",
            "destination": "CSTM",
            "route": "NDLS-CSTM",
            "stops": ["NDLS", "BPL", "CSTM"],
            "departure": "16:25",
            "arrival": "08:35+1",
        },
        {
            "number": "12001",
            "name": "Shatabdi Express",
            "type": TrainType.SHATABDI,
            "origin": "NDLS",
            "destination": "BPL",
            "route": "NDLS-CSTM",
            "stops": ["NDLS", "BPL"],
            "departure": "06:00",
            "arrival": "13:30",
        },
        {
            "number": "12002",
            "name": "Shatabdi Express",
            "type": TrainType.SHATABDI,
            "origin": "BPL",
            "destination": "NDLS",
            "route": "NDLS-CSTM",
            "stops": ["BPL", "NDLS"],
            "departure": "15:00",
            "arrival": "22:30",
        },
        {
            "number": "22691",
            "name": "Rajdhani Express",
            "type": TrainType.RAJDHANI,
            "origin": "NDLS",
            "destination": "SBC",
            "route": "NDLS-SBC",
            "stops": ["NDLS", "BPL", "NGP", "BZA", "SBC"],
            "departure": "20:50",
            "arrival": "06:00+2",
        },
        {
            "number": "12345",
            "name": "Sample Express",
            "type": TrainType.EXPRESS,
            "origin": "NDLS",
            "destination": "PNBE",
            "route": "NDLS-HWH",
            "stops": ["NDLS", "ALD", "PNBE"],
            "departure": "18:30",
            "arrival": "06:00+1",
        },
        {
            "number": "12346",
            "name": "Sample Express",
            "type": TrainType.EXPRESS,
            "origin": "PNBE",
            "destination": "NDLS",
            "route": "NDLS-HWH",
            "stops": ["PNBE", "ALD", "NDLS"],
            "departure": "18:30",
            "arrival": "06:00+1",
        },
    ]

    trains = []
    base_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    for i, data in enumerate(trains_data):
        origin_station = station_map[data["origin"]]
        dest_station = station_map[data["destination"]]
        route = route_map[data["route"]]

        dep_time_str = data["departure"]
        arr_time_str = data["arrival"]

        dep_hour, dep_min = map(int, dep_time_str.split(":"))
        scheduled_departure = base_date.replace(hour=dep_hour, minute=dep_min)

        if "+1" in arr_time_str:
            arr_time_str = arr_time_str.replace("+1", "")
            arr_day_offset = 1
        elif "+2" in arr_time_str:
            arr_time_str = arr_time_str.replace("+2", "")
            arr_day_offset = 2
        else:
            arr_day_offset = 0

        arr_hour, arr_min = map(int, arr_time_str.split(":"))
        scheduled_arrival = base_date.replace(hour=arr_hour, minute=arr_min) + timedelta(days=arr_day_offset)

        train = Train(
            id=i + 1,
            train_number=data["number"],
            train_name=data["name"],
            train_type=data["type"],
            origin_station_id=origin_station.id,
            destination_station_id=dest_station.id,
            route_id=route.id,
            total_stops=len(data["stops"]),
            total_distance_km=route.total_distance_km,
            scheduled_departure=scheduled_departure,
            scheduled_arrival=scheduled_arrival,
            status=TrainStatus.SCHEDULED,
            is_active=True,
        )
        trains.append(train)
        db.add(train)
        await db.flush()

        for seq, stop_code in enumerate(data["stops"]):
            stop_station = station_map[stop_code]
            is_origin = (seq == 0)
            is_dest = (seq == len(data["stops"]) - 1)

            if is_origin:
                sched_arr = None
                sched_dep = scheduled_departure
            elif is_dest:
                sched_arr = scheduled_arrival
                sched_dep = None
            else:
                fraction = seq / (len(data["stops"]) - 1)
                intermediate_time = scheduled_departure + (scheduled_arrival - scheduled_departure) * fraction
                sched_arr = intermediate_time - timedelta(minutes=2)
                sched_dep = intermediate_time + timedelta(minutes=2)

            distance = 0
            if seq > 0:
                prev_station = station_map[data["stops"][seq - 1]]
                section_result = await db.execute(
                    select(RouteSection).where(
                        RouteSection.route_id == route.id,
                        RouteSection.from_station_id == prev_station.id,
                        RouteSection.to_station_id == stop_station.id,
                    )
                )
                section = section_result.scalar_one_or_none()
                if section:
                    distance = section.distance_km

            schedule = TrainSchedule(
                train_id=train.id,
                station_id=stop_station.id,
                sequence=seq + 1,
                scheduled_arrival=sched_arr,
                scheduled_departure=sched_dep,
                scheduled_dwell_minutes=2 if not is_origin and not is_dest else 0,
                distance_from_origin_km=distance,
                is_origin=is_origin,
                is_destination=is_dest,
            )
            db.add(schedule)

    await db.flush()
    logger.info("Trains seeded", count=len(trains))
    return trains


async def seed_users(db: AsyncSession, stations: list[Station]) -> list[User]:
    """Create default users"""
    users_data = [
        {"username": "admin", "email": "admin@railintel.in", "name": "System Administrator", "role": UserRole.ADMIN, "password": "admin123", "station_id": None},
        {"username": "operator", "email": "operator@railintel.in", "name": "Control Room Operator", "role": UserRole.OPERATOR, "password": "operator123", "station_id": None},
        {"username": "supervisor", "email": "supervisor@railintel.in", "name": "Division Supervisor", "role": UserRole.SUPERVISOR, "password": "supervisor123", "station_id": stations[0].id},
        {"username": "station_master", "email": "sm.ndls@railintel.in", "name": "Station Master NDLS", "role": UserRole.STATION_STAFF, "password": "station123", "station_id": stations[0].id},
        {"username": "passenger", "email": "passenger@example.com", "name": "Demo Passenger", "role": UserRole.PASSENGER, "password": "passenger123", "station_id": None},
    ]

    users = []
    for data in users_data:
        user = User(
            username=data["username"],
            email=data["email"],
            full_name=data["name"],
            hashed_password=get_password_hash(data["password"]),
            role=data["role"],
            station_id=data["station_id"],
            is_active=True,
            is_verified=True,
        )
        users.append(user)
        db.add(user)

    await db.flush()
    logger.info("Users seeded", count=len(users))
    return users


async def main():
    await init_db()

    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting database seeding...")

            stations = await seed_stations(db)
            routes = await seed_routes(db, stations)
            trains = await seed_trains(db, stations, routes)
            users = await seed_users(db, stations)

            await db.commit()
            logger.info("Database seeding completed successfully!")
            logger.info(f"Created: {len(stations)} stations, {len(routes)} routes, {len(trains)} trains, {len(users)} users")

        except Exception as e:
            logger.error("Seeding failed", error=str(e))
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())