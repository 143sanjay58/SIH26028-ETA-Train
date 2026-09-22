import asyncio
import random
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.train import Train, TrainPosition, TrainSchedule, TrainStatus, TrainEvent
from backend.app.models.station import Station
from backend.app.models.route import Route, RouteSection
from backend.app.database.session import AsyncSessionLocal
from backend.app.schemas.simulation import SimulationScenario
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class SimulationState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


@dataclass
class TrainSimState:
    train: Train
    current_section_idx: int = 0
    position_in_section: float = 0.0
    current_speed: float = 0.0
    target_speed: float = 60.0
    dwell_timer: float = 0.0
    is_at_station: bool = True
    delay_minutes: float = 0.0
    last_station_departure: Optional[datetime] = None


class SimulationEngine:
    def __init__(self):
        self.state = SimulationState.STOPPED
        self.speed_multiplier = settings.simulation_speed
        self.scenario = SimulationScenario(settings.simulation_scenario.upper())
        self.trains: Dict[int, TrainSimState] = {}
        self.callbacks: List[Callable] = []
        self.simulation_time = datetime.now(timezone.utc)
        self._task: Optional[asyncio.Task] = None
        self._db_session: Optional[AsyncSession] = None

    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    async def start(self):
        if self.state == SimulationState.RUNNING:
            return

        if self.state == SimulationState.PAUSED:
            self.state = SimulationState.RUNNING
            logger.info("Simulation restarted from pause")
            return

        await self._initialize()
        self.state = SimulationState.RUNNING
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Simulation started", speed=self.speed_multiplier, scenario=self.scenario.value)

    async def pause(self):
        if self.state == SimulationState.RUNNING:
            self.state = SimulationState.PAUSED
            logger.info("Simulation paused")

    async def resume(self):
        if self.state == SimulationState.PAUSED:
            self.state = SimulationState.RUNNING
            logger.info("Simulation resumed")

    async def stop(self):
        self.state = SimulationState.STOPPED
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Simulation stopped")

    async def set_speed(self, speed: float):
        self.speed_multiplier = max(0.1, min(10.0, speed))
        logger.info("Simulation speed changed", speed=self.speed_multiplier)

    async def set_scenario(self, scenario: SimulationScenario):
        self.scenario = scenario
        logger.info("Simulation scenario changed", scenario=scenario.value)

    async def _initialize(self):
        self._db_session = AsyncSessionLocal()
        try:
            trains_result = await self._db_session.execute(
                select(Train)
                .options(selectinload(Train.schedules).selectinload(TrainSchedule.station))
                .where(Train.is_active == True, Train.status.in_([TrainStatus.SCHEDULED, TrainStatus.RUNNING]))
            )
            trains = trains_result.scalars().all()

            for train in trains:
                schedules = train.schedules

                if not schedules:
                    continue

                first_station = schedules[0].station
                sim_state = TrainSimState(
                    train=train,
                    current_section_idx=0,
                    position_in_section=0.0,
                    current_speed=0.0,
                    target_speed=self._get_base_speed(train),
                    is_at_station=True,
                    dwell_timer=0.0,
                    delay_minutes=0.0,
                )
                self.trains[train.id] = sim_state

                await self._update_train_status(train.id, TrainStatus.RUNNING)
                await self._create_initial_position(train, first_station)

            self.simulation_time = datetime.now(timezone.utc)
        finally:
            await self._db_session.close()
            self._db_session = None

    def _get_base_speed(self, train: Train) -> float:
        speeds = {
            "VANDE_BHARAT": 160,
            "RAJDHANI": 130,
            "SHATABDI": 130,
            "DURONTO": 130,
            "SUPERFAST": 110,
            "EXPRESS": 90,
            "MAIL": 80,
            "PASSENGER": 60,
            "SUBURBAN": 50,
            "FREIGHT": 40,
        }
        return speeds.get(train.train_type.value, 80)

    async def _create_initial_position(self, train: Train, station: Station):
        position = TrainPosition(
            train_id=train.id,
            latitude=station.latitude + random.uniform(-0.001, 0.001),
            longitude=station.longitude + random.uniform(-0.001, 0.001),
            speed_kmh=0.0,
            current_station_id=station.id,
            distance_travelled_km=0.0,
            delay_minutes=0,
            timestamp=datetime.now(timezone.utc),
            source="SIMULATION",
        )
        self._db_session.add(position)
        await self._db_session.flush()

    async def _run_loop(self):
        try:
            while self.state != SimulationState.STOPPED:
                if self.state == SimulationState.RUNNING:
                    start_time = datetime.now(timezone.utc)
                    await self._simulation_step()
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    sleep_time = max(0, 1.0 / self.speed_multiplier - elapsed)
                    await asyncio.sleep(sleep_time)
                else:
                    await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Simulation loop error", error=str(e))
            await self.stop()

    async def _simulation_step(self):
        self._db_session = AsyncSessionLocal()
        try:
            self.simulation_time += timedelta(seconds=1 * self.speed_multiplier)

            for train_id, sim_state in self.trains.items():
                await self._update_train_simulation(train_id, sim_state)

            await self._db_session.commit()
            await self._notify_callbacks()
        except Exception as e:
            logger.error("Simulation step error", error=str(e))
            await self._db_session.rollback()
        finally:
            await self._db_session.close()
            self._db_session = None

    async def _update_train_simulation(self, train_id: int, sim_state: TrainSimState):
        train = sim_state.train

        schedule_result = await self._db_session.execute(
            select(TrainSchedule)
            .where(TrainSchedule.train_id == train_id)
            .order_by(TrainSchedule.sequence)
        )
        schedules = list(schedule_result.scalars().all())

        if not schedules or sim_state.current_section_idx >= len(schedules) - 1:
            await self._complete_journey(train_id)
            return

        current_schedule = schedules[sim_state.current_section_idx]
        next_schedule = schedules[sim_state.current_section_idx + 1]

        current_station = await self._db_session.get(Station, current_schedule.station_id)
        next_station = await self._db_session.get(Station, next_schedule.station_id)

        section_result = await self._db_session.execute(
            select(RouteSection)
            .where(
                RouteSection.route_id == train.route_id,
                RouteSection.from_station_id == current_schedule.station_id,
                RouteSection.to_station_id == next_schedule.station_id,
            )
        )
        section = section_result.scalar_one_or_none()

        if not section:
            return

        if sim_state.is_at_station:
            await self._handle_station_dwell(train_id, sim_state, current_schedule, current_station)
        else:
            await self._handle_section_travel(train_id, sim_state, section, current_station, next_station)

    async def _handle_station_dwell(
        self, train_id: int, sim_state: TrainSimState, schedule: TrainSchedule, station: Station
    ):
        scheduled_dwell = schedule.scheduled_dwell_minutes * 60
        dwell_limit = scheduled_dwell

        if self.scenario == SimulationScenario.EXTENDED_HALT and random.random() < 0.1:
            dwell_limit *= random.uniform(3, 6)
        elif self.scenario == SimulationScenario.CONGESTION and random.random() < 0.05:
            dwell_limit *= random.uniform(2, 4)

        sim_state.dwell_timer += 1 * self.speed_multiplier

        if sim_state.dwell_timer >= dwell_limit:
            sim_state.is_at_station = False
            sim_state.dwell_timer = 0.0
            sim_state.position_in_section = 0.0
            sim_state.current_speed = 0.0
            sim_state.target_speed = self._get_target_speed(section=sim_state.train)
            sim_state.last_station_departure = datetime.now(timezone.utc)

            await self._create_departure_event(train_id, station, sim_state.delay_minutes)
        else:
            await self._update_position_at_station(train_id, station, sim_state)

    async def _handle_section_travel(
        self,
        train_id: int,
        sim_state: TrainSimState,
        section: RouteSection,
        from_station: Station,
        to_station: Station,
    ):
        base_speed = sim_state.target_speed
        speed_factor = 1.0

        if self.scenario == SimulationScenario.SPEED_RESTRICTION:
            speed_factor *= 0.5
        elif self.scenario == SimulationScenario.HEAVY_RAIN:
            speed_factor *= 0.7
        elif self.scenario == SimulationScenario.LOW_VISIBILITY:
            speed_factor *= 0.6
        elif self.scenario == SimulationScenario.CONGESTION:
            speed_factor *= random.uniform(0.5, 0.8)

        if random.random() < 0.02:
            speed_factor *= random.uniform(0.3, 0.7)

        target = base_speed * speed_factor
        sim_state.current_speed += (target - sim_state.current_speed) * 0.1
        sim_state.current_speed = max(0, min(sim_state.current_speed, section.max_speed_kmh))

        distance_step = (sim_state.current_speed / 3600) * self.speed_multiplier
        sim_state.position_in_section += distance_step

        progress = sim_state.position_in_section / section.distance_km if section.distance_km > 0 else 1.0

        lat = from_station.latitude + (to_station.latitude - from_station.latitude) * progress
        lon = from_station.longitude + (to_station.longitude - from_station.longitude) * progress

        distance_travelled = sim_state.position_in_section
        if sim_state.current_section_idx > 0:
            prev_sections_result = await self._db_session.execute(
                select(RouteSection.distance_km)
                .where(
                    RouteSection.route_id == sim_state.train.route_id,
                    RouteSection.sequence <= sim_state.current_section_idx,
                )
            )
            distance_travelled += sum(r[0] for r in prev_sections_result.all())

        delay = self._calculate_delay(sim_state, section, progress)
        sim_state.delay_minutes = delay

        position = TrainPosition(
            train_id=train_id,
            latitude=lat,
            longitude=lon,
            speed_kmh=sim_state.current_speed,
            current_station_id=None,
            next_station_id=to_station.id,
            distance_to_next_km=section.distance_km * (1 - progress),
            distance_travelled_km=distance_travelled,
            delay_minutes=int(delay),
            timestamp=self.simulation_time,
            source="SIMULATION",
        )
        self._db_session.add(position)

        if progress >= 1.0:
            sim_state.is_at_station = True
            sim_state.current_section_idx += 1
            sim_state.position_in_section = 0.0
            sim_state.current_speed = 0.0
            sim_state.dwell_timer = 0.0

            await self._create_arrival_event(train_id, to_station, delay)

    def _calculate_delay(self, sim_state: TrainSimState, section: RouteSection, progress: float) -> float:
        scheduled_time = section.scheduled_travel_time_minutes
        actual_time_elapsed = (self.simulation_time - sim_state.last_station_departure).total_seconds() / 60 if sim_state.last_station_departure else 0
        return max(0, actual_time_elapsed - scheduled_time)

    async def _update_position_at_station(self, train_id: int, station: Station, sim_state: TrainSimState):
        position = TrainPosition(
            train_id=train_id,
            latitude=station.latitude,
            longitude=station.longitude,
            speed_kmh=0.0,
            current_station_id=station.id,
            next_station_id=None,
            distance_to_next_km=None,
            distance_travelled_km=0.0,
            delay_minutes=int(sim_state.delay_minutes),
            timestamp=self.simulation_time,
            source="SIMULATION",
        )
        self._db_session.add(position)

    async def _create_arrival_event(self, train_id: int, station: Station, delay: float):
        event = TrainEvent(
            train_id=train_id,
            station_id=station.id,
            event_type="ARRIVAL",
            description=f"Arrived at {station.name}",
            delay_minutes=int(delay),
            timestamp=self.simulation_time,
            source="SIMULATION",
        )
        self._db_session.add(event)

    async def _create_departure_event(self, train_id: int, station: Station, delay: float):
        event = TrainEvent(
            train_id=train_id,
            station_id=station.id,
            event_type="DEPARTURE",
            description=f"Departed from {station.name}",
            delay_minutes=int(delay),
            timestamp=self.simulation_time,
            source="SIMULATION",
        )
        self._db_session.add(event)

    async def _complete_journey(self, train_id: int):
        sim_state = self.trains.get(train_id)
        if sim_state:
            await self._update_train_status(train_id, TrainStatus.ARRIVED)
            event = TrainEvent(
                train_id=train_id,
                event_type="JOURNEY_COMPLETE",
                description="Journey completed",
                delay_minutes=int(sim_state.delay_minutes),
                timestamp=self.simulation_time,
                source="SIMULATION",
            )
            self._db_session.add(event)
            logger.info("Train journey completed", train_id=train_id)

    async def _update_train_status(self, train_id: int, status: TrainStatus):
        train = await self._db_session.get(Train, train_id)
        if train:
            train.status = status
            train.updated_at = datetime.now(timezone.utc)

    async def _notify_callbacks(self):
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.get_status())
                else:
                    callback(self.get_status())
            except Exception as e:
                logger.error("Callback error", error=str(e))

    def get_status(self):
        return {
            "state": self.state.value,
            "speed": self.speed_multiplier,
            "scenario": self.scenario.value,
            "active_trains": len([t for t in self.trains.values() if t.train.status != TrainStatus.ARRIVED]),
            "simulation_time": self.simulation_time.isoformat(),
        }


simulation_engine = SimulationEngine()