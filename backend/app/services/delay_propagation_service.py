from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.train import Train, TrainPosition, TrainSchedule
from backend.app.models.route import RouteSection
from backend.app.models.station import Station
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class DelayPropagationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def propagate_delay(
        self,
        train_id: int,
        current_station_id: Optional[int],
        current_delay_minutes: int,
    ) -> List[Dict[str, Any]]:
        train = await self.db.get(Train, train_id)
        if not train:
            return []

        schedule_result = await self.db.execute(
            select(TrainSchedule)
            .options(selectinload(TrainSchedule.station))
            .where(TrainSchedule.train_id == train_id)
            .order_by(TrainSchedule.sequence)
        )
        all_stops = list(schedule_result.scalars().all())

        if not all_stops:
            return []

        current_idx = 0
        if current_station_id:
            for i, stop in enumerate(all_stops):
                if stop.station_id == current_station_id:
                    current_idx = i
                    break

        propagation = []
        remaining_delay = float(current_delay_minutes)

        for i in range(current_idx, len(all_stops) - 1):
            current_stop = all_stops[i]
            next_stop = all_stops[i + 1]

            section_result = await self.db.execute(
                select(RouteSection)
                .where(
                    and_(
                        RouteSection.route_id == train.route_id,
                        RouteSection.from_station_id == current_stop.station_id,
                        RouteSection.to_station_id == next_stop.station_id,
                    )
                )
            )
            section = section_result.scalar_one_or_none()

            if not section:
                continue

            recovery = self._calculate_recovery(section, remaining_delay)
            congestion = self._calculate_congestion_impact(section, train_id)
            signal_delay = self._calculate_signal_delay(section)
            section_delay = congestion + signal_delay

            remaining_delay = max(0, remaining_delay - recovery + section_delay)

            propagation.append({
                "from_station": current_stop.station.name,
                "to_station": next_stop.station.name,
                "section_distance_km": section.distance_km,
                "scheduled_travel_time": section.scheduled_travel_time_minutes,
                "delay_at_departure": max(0, remaining_delay - section_delay),
                "recovery_minutes": recovery,
                "congestion_delay": congestion,
                "signal_delay": signal_delay,
                "net_section_delay": section_delay - recovery,
                "delay_at_arrival": remaining_delay,
            })

            current_station_id = next_stop.station_id

        destination = all_stops[-1].station
        propagation.append({
            "destination": destination.name,
            "final_predicted_delay": remaining_delay,
            "total_propagation_stages": len(propagation),
        })

        return propagation

    def _calculate_recovery(self, section: RouteSection, current_delay: float) -> float:
        if current_delay <= 0:
            return 0.0

        max_recovery = section.historical_recovery_minutes or 0
        if max_recovery <= 0:
            return 0.0

        recovery_factor = min(1.0, current_delay / 30.0)
        return max_recovery * recovery_factor

    def _calculate_congestion_impact(self, section: RouteSection, train_id: int) -> float:
        return 0.0

    def _calculate_signal_delay(self, section: RouteSection) -> float:
        return 0.0

    async def get_delay_chain(self, train_id: int) -> List[Dict[str, Any]]:
        train = await self.db.get(Train, train_id)
        if not train:
            return []

        position_result = await self.db.execute(
            select(TrainPosition)
            .where(TrainPosition.train_id == train_id)
            .order_by(TrainPosition.timestamp.desc())
            .limit(1)
        )
        position = position_result.scalar_one_or_none()

        if not position:
            return []

        return await self.propagate_delay(train_id, position.current_station_id, position.delay_minutes)