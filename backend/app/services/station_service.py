from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.station import (
    Station,
    StationReport,
    StationEvent,
    StationType,
    StationReportStatus,
    StationReportEventType,
    StationSeverity,
)
from backend.app.models.train import Train
from backend.app.schemas.station import StationCreate, StationUpdate, StationReportCreate, StationReportUpdate
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class StationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_station(self, station_data: StationCreate) -> Station:
        station = Station(**station_data.model_dump())
        self.db.add(station)
        await self.db.flush()
        await self.db.refresh(station)
        logger.info("Station created", station_id=station.id, code=station.code)
        return station

    async def get_station_by_id(self, station_id: int) -> Optional[Station]:
        result = await self.db.execute(
            select(Station).where(Station.id == station_id)
        )
        return result.scalar_one_or_none()

    async def get_station_by_code(self, code: str) -> Optional[Station]:
        result = await self.db.execute(
            select(Station).where(Station.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def get_stations(
        self,
        page: int = 1,
        page_size: int = 50,
        station_type: Optional[StationType] = None,
        state: Optional[str] = None,
        zone: Optional[str] = None,
        is_junction: Optional[bool] = None,
    ) -> tuple[List[Station], int]:
        query = select(Station)

        conditions = [Station.is_active == True]
        if station_type:
            conditions.append(Station.station_type == station_type)
        if state:
            conditions.append(Station.state == state)
        if zone:
            conditions.append(Station.zone == zone)
        if is_junction is not None:
            conditions.append(Station.is_junction == is_junction)

        query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(Station.code).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        stations = result.scalars().all()

        return list(stations), total

    async def update_station(self, station_id: int, station_data: StationUpdate) -> Optional[Station]:
        station = await self.get_station_by_id(station_id)
        if not station:
            return None

        update_data = station_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(station, field, value)

        station.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(station)
        logger.info("Station updated", station_id=station.id)
        return station

    async def create_station_report(
        self, report_data: StationReportCreate, reported_by_user_id: int
    ) -> StationReport:
        report = StationReport(**report_data.model_dump(), reported_by_user_id=reported_by_user_id)
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        logger.info("Station report created", report_id=report.id, train_id=report.train_id)
        return report

    async def get_station_report(self, report_id: int) -> Optional[StationReport]:
        result = await self.db.execute(
            select(StationReport)
            .options(
                selectinload(StationReport.train),
                selectinload(StationReport.station),
                selectinload(StationReport.reported_by),
                selectinload(StationReport.verified_by),
            )
            .where(StationReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_station_reports(
        self,
        station_id: Optional[int] = None,
        train_id: Optional[int] = None,
        status: Optional[StationReportStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[StationReport], int]:
        query = select(StationReport).options(
            selectinload(StationReport.train),
            selectinload(StationReport.station),
            selectinload(StationReport.reported_by),
        )

        conditions = []
        if station_id:
            conditions.append(StationReport.station_id == station_id)
        if train_id:
            conditions.append(StationReport.train_id == train_id)
        if status:
            conditions.append(StationReport.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(desc(StationReport.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        reports = result.scalars().all()

        return list(reports), total

    async def update_station_report(
        self, report_id: int, report_data: StationReportUpdate, user_id: Optional[int] = None
    ) -> Optional[StationReport]:
        report = await self.get_station_report(report_id)
        if not report:
            return None

        update_data = report_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(report, field, value)

        if report_data.status == StationReportStatus.VERIFIED and user_id:
            report.verified_by_user_id = user_id

        if report_data.status == StationReportStatus.RESOLVED:
            report.actual_resolution = datetime.now(timezone.utc)

        report.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(report)
        logger.info("Station report updated", report_id=report.id, status=report.status)
        return report

    async def get_station_events(
        self,
        station_id: int,
        train_id: Optional[int] = None,
        limit: int = 50,
        since: Optional[datetime] = None,
    ) -> List[StationEvent]:
        query = select(StationEvent).where(StationEvent.station_id == station_id)
        if train_id:
            query = query.where(StationEvent.train_id == train_id)
        if since:
            query = query.where(StationEvent.actual_time >= since)
        query = query.order_by(desc(StationEvent.actual_time)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_station_event(
        self,
        station_id: int,
        event_type: str,
        description: str,
        train_id: Optional[int] = None,
        scheduled_time: Optional[datetime] = None,
        dwell_minutes: Optional[int] = None,
        expected_dwell_minutes: Optional[int] = None,
        source: str = "SYSTEM",
        metadata: Optional[dict] = None,
    ) -> StationEvent:
        is_extended = False
        extended_minutes = None
        if dwell_minutes is not None and expected_dwell_minutes is not None:
            if dwell_minutes > expected_dwell_minutes:
                is_extended = True
                extended_minutes = dwell_minutes - expected_dwell_minutes

        event = StationEvent(
            station_id=station_id,
            train_id=train_id,
            event_type=event_type,
            description=description,
            scheduled_time=scheduled_time,
            actual_time=datetime.now(timezone.utc),
            dwell_minutes=dwell_minutes,
            expected_dwell_minutes=expected_dwell_minutes,
            is_extended_halt=is_extended,
            extended_minutes=extended_minutes,
            source=source,
            event_metadata=metadata,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def check_extended_halt(
        self, train_id: int, station_id: int, actual_dwell_minutes: int
    ) -> Optional[StationEvent]:
        schedule_result = await self.db.execute(
            select(TrainSchedule.scheduled_dwell_minutes)
            .where(
                and_(
                    TrainSchedule.train_id == train_id,
                    TrainSchedule.station_id == station_id,
                )
            )
        )
        expected_dwell = schedule_result.scalar_one_or_none() or 2

        if actual_dwell_minutes > expected_dwell_minutes + 5:
            event = await self.add_station_event(
                station_id=station_id,
                train_id=train_id,
                event_type="EXTENDED_HALT",
                description=f"Extended halt detected: {actual_dwell_minutes} min vs expected {expected_dwell_minutes} min",
                dwell_minutes=actual_dwell_minutes,
                expected_dwell_minutes=expected_dwell_minutes,
                source="DETECTION",
            )
            return event
        return None