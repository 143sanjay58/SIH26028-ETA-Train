from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.train import Train, TrainPosition, TrainSchedule, TrainEvent, TrainStatus, TrainType
from backend.app.models.station import Station
from backend.app.models.route import Route, RouteSection
from backend.app.schemas.train import TrainCreate, TrainUpdate, TrainPositionCreate
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class TrainService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_train(self, train_data: TrainCreate) -> Train:
        train = Train(**train_data.model_dump())
        self.db.add(train)
        await self.db.flush()
        await self.db.refresh(train)
        logger.info("Train created", train_id=train.id, train_number=train.train_number)
        return train

    async def get_train_by_id(self, train_id: int) -> Optional[Train]:
        result = await self.db.execute(
            select(Train)
            .options(
                selectinload(Train.origin_station),
                selectinload(Train.destination_station),
                selectinload(Train.route).selectinload(Route.sections),
            )
            .where(Train.id == train_id)
        )
        return result.scalar_one_or_none()

    async def get_train_by_number(self, train_number: str) -> Optional[Train]:
        result = await self.db.execute(
            select(Train)
            .options(
                selectinload(Train.origin_station),
                selectinload(Train.destination_station),
                selectinload(Train.route),
            )
            .where(Train.train_number == train_number)
        )
        return result.scalar_one_or_none()

    async def get_trains(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[TrainStatus] = None,
        train_type: Optional[TrainType] = None,
        route_id: Optional[int] = None,
    ) -> tuple[List[Train], int]:
        query = select(Train).options(
            selectinload(Train.origin_station),
            selectinload(Train.destination_station),
        )

        conditions = [Train.is_active == True]
        if status:
            conditions.append(Train.status == status)
        if train_type:
            conditions.append(Train.train_type == train_type)
        if route_id:
            conditions.append(Train.route_id == route_id)

        query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(Train.train_number).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        trains = result.scalars().all()

        return list(trains), total

    async def update_train(self, train_id: int, train_data: TrainUpdate) -> Optional[Train]:
        train = await self.get_train_by_id(train_id)
        if not train:
            return None

        update_data = train_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(train, field, value)

        train.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(train)
        logger.info("Train updated", train_id=train.id)
        return train

    async def delete_train(self, train_id: int) -> bool:
        train = await self.get_train_by_id(train_id)
        if not train:
            return False

        train.is_active = False
        train.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        logger.info("Train deactivated", train_id=train.id)
        return True

    async def get_latest_position(self, train_id: int) -> Optional[TrainPosition]:
        result = await self.db.execute(
            select(TrainPosition)
            .options(
                selectinload(TrainPosition.current_station),
                selectinload(TrainPosition.next_station),
            )
            .where(TrainPosition.train_id == train_id)
            .order_by(desc(TrainPosition.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_positions(
        self,
        train_id: int,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[TrainPosition]:
        query = select(TrainPosition).where(TrainPosition.train_id == train_id)
        if since:
            query = query.where(TrainPosition.timestamp >= since)
        query = query.order_by(desc(TrainPosition.timestamp)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_position(self, position_data: TrainPositionCreate) -> TrainPosition:
        position = TrainPosition(**position_data.model_dump())
        self.db.add(position)

        train = await self.get_train_by_id(position_data.train_id)
        if train:
            train.status = TrainStatus.RUNNING if position_data.speed_kmh > 0 else TrainStatus.DELAYED
            if position_data.delay_minutes > 0:
                train.status = TrainStatus.DELAYED

        await self.db.flush()
        await self.db.refresh(position)
        return position

    async def get_schedule(self, train_id: int) -> List[TrainSchedule]:
        result = await self.db.execute(
            select(TrainSchedule)
            .options(selectinload(TrainSchedule.station))
            .where(TrainSchedule.train_id == train_id)
            .order_by(TrainSchedule.sequence)
        )
        return list(result.scalars().all())

    async def get_upcoming_stations(self, train_id: int, limit: int = 5) -> List[TrainSchedule]:
        position = await self.get_latest_position(train_id)
        if not position:
            return []
        if not position.current_station_id and not position.next_station_id:
            return []

        anchor_station_id = position.current_station_id or position.next_station_id
        current_seq_result = await self.db.execute(
            select(TrainSchedule.sequence)
            .where(
                and_(
                    TrainSchedule.train_id == train_id,
                    TrainSchedule.station_id == anchor_station_id,
                )
            )
        )
        current_seq = current_seq_result.scalar_one_or_none()
        if current_seq is None:
            return []

        if position.current_station_id is None:
            current_seq = max(0, current_seq - 1)

        result = await self.db.execute(
            select(TrainSchedule)
            .options(selectinload(TrainSchedule.station))
            .where(
                and_(
                    TrainSchedule.train_id == train_id,
                    TrainSchedule.sequence > current_seq,
                )
            )
            .order_by(TrainSchedule.sequence)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_events(
        self,
        train_id: int,
        limit: int = 50,
        since: Optional[datetime] = None,
    ) -> List[TrainEvent]:
        query = select(TrainEvent).where(TrainEvent.train_id == train_id)
        if since:
            query = query.where(TrainEvent.timestamp >= since)
        query = query.order_by(desc(TrainEvent.timestamp)).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_event(
        self,
        train_id: int,
        event_type: str,
        description: str,
        delay_minutes: int = 0,
        station_id: Optional[int] = None,
        source: str = "SYSTEM",
        metadata: Optional[dict] = None,
    ) -> TrainEvent:
        event = TrainEvent(
            train_id=train_id,
            station_id=station_id,
            event_type=event_type,
            description=description,
            delay_minutes=delay_minutes,
            source=source,
            event_metadata=metadata,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event