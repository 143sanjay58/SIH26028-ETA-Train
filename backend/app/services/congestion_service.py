from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.train import Train, TrainPosition
from backend.app.models.route import RouteSection
from backend.app.models.congestion import CongestionState, CongestionLevel
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class CongestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_section_congestion(
        self, section_id: int, time_window_minutes: int = 10
    ) -> CongestionState:
        since = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)

        positions_result = await self.db.execute(
            select(TrainPosition)
            .join(Train, Train.id == TrainPosition.train_id)
            .where(
                and_(
                    TrainPosition.timestamp >= since,
                    TrainPosition.is_valid == True,
                )
            )
        )
        positions = positions_result.scalars().all()

        section = await self.db.get(RouteSection, section_id)
        if not section:
            raise ValueError(f"Section {section_id} not found")

        section_positions = [
            p for p in positions
            if self._is_in_section(p, section)
        ]

        train_count = len({p.train_id for p in section_positions})
        length_km = section.distance_km
        density = train_count / length_km if length_km > 0 else 0

        speeds = [p.speed_kmh for p in section_positions if p.speed_kmh > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else None

        delays = [p.delay_minutes for p in section_positions]
        avg_delay = sum(delays) / len(delays) if delays else 0

        level = self._determine_congestion_level(density, avg_speed, avg_delay)

        preceding_delay = await self._get_preceding_train_delay(section_id, section_positions)
        following_delay = await self._get_following_train_delay(section_id, section_positions)

        congestion = CongestionState(
            section_id=section_id,
            train_count=train_count,
            train_density_per_km=density,
            avg_speed_kmh=avg_speed,
            avg_delay_minutes=avg_delay,
            preceding_train_delay_minutes=preceding_delay,
            following_train_delay_minutes=following_delay,
            level=level,
            historical_congestion_score=self._get_historical_score(section),
            measured_at=datetime.now(timezone.utc),
        )

        self.db.add(congestion)
        await self.db.flush()
        return congestion

    def _is_in_section(self, position: TrainPosition, section: RouteSection) -> bool:
        if not position.current_station_id:
            return False
        return position.current_station_id == section.from_station_id

    def _determine_congestion_level(
        self, density: float, avg_speed: Optional[float], avg_delay: float
    ) -> CongestionLevel:
        if density > 3.0 or (avg_speed is not None and avg_speed < 20) or avg_delay > 30:
            return CongestionLevel.CRITICAL
        elif density > 1.5 or (avg_speed is not None and avg_speed < 40) or avg_delay > 15:
            return CongestionLevel.HIGH
        elif density > 0.5 or (avg_speed is not None and avg_speed < 60) or avg_delay > 5:
            return CongestionLevel.MEDIUM
        return CongestionLevel.LOW

    async def _get_preceding_train_delay(
        self, section_id: int, positions: List[TrainPosition]
    ) -> Optional[float]:
        if not positions:
            return None
        max_delay = max(p.delay_minutes for p in positions)
        return float(max_delay) if max_delay > 0 else None

    async def _get_following_train_delay(
        self, section_id: int, positions: List[TrainPosition]
    ) -> Optional[float]:
        return None

    def _get_historical_score(self, section: RouteSection) -> Optional[float]:
        if section.historical_delay_probability is not None:
            return section.historical_delay_probability * 100
        return None

    async def calculate_station_congestion(
        self, station_id: int, time_window_minutes: int = 30
    ) -> CongestionState:
        since = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)

        positions_result = await self.db.execute(
            select(TrainPosition)
            .where(
                and_(
                    TrainPosition.current_station_id == station_id,
                    TrainPosition.timestamp >= since,
                    TrainPosition.is_valid == True,
                )
            )
        )
        positions = positions_result.scalars().all()

        train_count = len({p.train_id for p in positions})
        avg_delay = sum(p.delay_minutes for p in positions) / len(positions) if positions else 0

        level = CongestionLevel.LOW
        if train_count > 5:
            level = CongestionLevel.CRITICAL
        elif train_count > 3:
            level = CongestionLevel.HIGH
        elif train_count > 1:
            level = CongestionLevel.MEDIUM

        congestion = CongestionState(
            section_id=None,
            station_id=station_id,
            train_count=train_count,
            train_density_per_km=0,
            avg_speed_kmh=None,
            avg_delay_minutes=avg_delay,
            level=level,
            measured_at=datetime.now(timezone.utc),
        )

        self.db.add(congestion)
        await self.db.flush()
        return congestion

    async def get_network_congestion(self) -> List[CongestionState]:
        result = await self.db.execute(
            select(CongestionState)
            .where(CongestionState.measured_at >= datetime.now(timezone.utc) - timedelta(minutes=15))
            .order_by(CongestionState.measured_at.desc())
        )
        return list(result.scalars().all())