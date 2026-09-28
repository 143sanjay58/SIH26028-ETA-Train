"""
Integration service that drives the embedded SIH26028 ETA core from the
teammate platform's live train state.

Responsibilities:
  - Map a teammate Train + latest TrainPosition + TrainSchedule into the
    universal TrainState contract of the 21-feature LightGBM pipeline.
  - Resolve teammate station codes onto the frozen route dataset's
    route_order positions (from_station of segment N == node N).
  - Run the SIH DynamicETAEngine (with its monotonic ETA consistency
    correction) and return a unified, richer ETA response that also carries
    confidence level and delay-impact signals.
  - Trains absent from the frozen route dataset raise SIHETANotCovered; the
    API layer falls back to the teammate's existing ETA service untouched.

The core engine is loaded lazily (the route CSV + LightGBM jobs are heavy);
only the first SIH request pays the cold-start cost.
"""
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.train import Train, TrainPosition
from backend.app.models.station import Station
from backend.app.schemas.common import DataSource
from backend.app.services.train_service import TrainService
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

_engine = None
_lock = threading.Lock()


class SIHETANotCovered(ValueError):
    """Train is not represented in the SIH26028 frozen route dataset."""


def _get_engine():
    """Lazily instantiate + cache the SIH26028 DynamicETAEngine singleton."""
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                from dynamic_eta_engine import DynamicETAEngine

                logger.info("Loading SIH26028 ETA engine (route data + LightGBM models)...")
                _engine = DynamicETAEngine()
                _install_route_cache(_engine)
                logger.info("SIH26028 ETA engine ready.")
    return _engine


def _install_route_cache(engine):
    """Install a process-local, per-train route cache on the SIH ETA engine.

    Why it exists
    -------------
    The SIH ETA core rebuilds a train's route from the full 372,911-row
    timetable for EVERY predicted station, twice: once through
    DynamicETAEngine._get_train_route() (used by ``_scheduled_remaining`` and
    station-to-route mapping) and once through FeatureBuilder.get_train_route()
    (used by FeatureBuilder.build()). Those redundant full-table scans dominate
    prediction latency (measured ~88% of the per-station feature-building cost).

    The timetable is frozen/validated data, so once a route is built it never
    needs rebuilding. This cache keeps a single sorted route DataFrame per
    normalized train number and serves both route consumers from it.

    What it does NOT change
    -----------------------
    - No ETA/model math is altered: cached routes hold the same rows, ordering
      and timetable values the core would have produced, so the 21 features and
      every downstream ETA/delay/confidence/impact value are unchanged.
    - Both consumers only read (mask/filter/slice) the returned route; they
      never mutate it, so sharing one cached object is safe.
    - Process-local memory only: nothing is written to disk, no cache
      invalidation (frozen data), no external dependencies.
    """
    route_cache = {}
    engine_get_train_route = engine._get_train_route

    def cached_get_train_route(train_number):
        # Same normalization the SIH core uses: strip leading zeros.
        key = str(train_number).strip().lstrip("0") or "0"
        if key not in route_cache:
            route_cache[key] = engine_get_train_route(train_number)
        return route_cache[key]

    engine._get_train_route = cached_get_train_route
    engine.predictor.feature_builder.get_train_route = cached_get_train_route


class SIHETAService:
    """Primary ETA service for trains covered by the SIH26028 core dataset."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.train_service = TrainService(db)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def predict_eta(self, train_number: str) -> Dict[str, Any]:
        train = await self.train_service.get_train_by_number(train_number)
        if train is not None:
            return await self._predict_from_train(train)

        return await self._predict_from_catalogue(train_number)

    async def _predict_from_train(self, train: Train) -> Dict[str, Any]:
        position = await self.train_service.get_latest_position(train.id)
        if not position:
            raise ValueError(f"No position data for train {train.train_number}")

        station = await self._resolve_current_station(train, position)

        engine = _get_engine()
        position_on_route = self._map_station_to_route_position(
            engine, train.train_number, station.code
        )

        state = self._build_train_state(
            train_number=train.train_number,
            position=position,
            station_code=station.code,
            route_position=position_on_route,
        )

        results = engine.update_state(state)

        return self._build_response(
            train_number=train.train_number,
            train_name=train.train_name,
            station_name=station.name,
            state=state,
            results=results,
            position_source=position.source,
        )

    async def _predict_from_catalogue(self, train_number: str) -> Dict[str, Any]:
        from backend.app.services.sih_catalogue import CATALOGUE_SOURCE, get_catalogue

        catalogue = get_catalogue()
        route = catalogue.get_route(train_number)
        if not route:
            raise SIHETANotCovered(
                f"Train {train_number} is not in the SIH catalogue"
            )

        engine = _get_engine()

        first = route[0]
        station_code = str(first["from_station"]).strip().upper()
        station_name = first.get("from_station_name") or station_code
        current_time = datetime.now(timezone.utc)

        from train_state import TrainState

        state = TrainState(
            train_number=str(train_number).strip().lstrip("0") or "0",
            current_station=station_code,
            current_route_position=int(first["route_order"]),
            current_arrival_delay=0.0,
            current_departure_delay=0.0,
            current_time=current_time,
        )

        results = engine.update_state(state)

        return self._build_response(
            train_number=str(train_number).strip(),
            train_name=f"SIH CATALOGUE TRAIN {train_number}",
            station_name=station_name,
            state=state,
            results=results,
            position_source=CATALOGUE_SOURCE,
        )

    # ------------------------------------------------------------------
    # State resolution
    # ------------------------------------------------------------------

    async def _resolve_current_station(
        self, train: Train, position: TrainPosition
    ) -> Station:
        """Return the last station passed.

        - At a station  -> that station (position.current_station_id).
        - Between stops -> the schedule station immediately before the
          upcoming next station.
        - Otherwise     -> the origin schedule station.
        """
        if position.current_station_id is not None:
            station = await self.db.get(Station, position.current_station_id)
            if station:
                return station

        schedules = await self.train_service.get_schedule(train.id)
        if not schedules:
            raise ValueError(f"No schedule data for train {train.train_number}")

        if position.next_station_id is not None:
            for idx, schedule in enumerate(schedules):
                if schedule.station_id == position.next_station_id:
                    if idx > 0:
                        return schedules[idx - 1].station
        return schedules[0].station

    def _map_station_to_route_position(self, engine, train_number: str, station_code: str) -> int:
        """Map a station code to its route_order node index in the dataset.

        route_order N connects node N -> N+1, so a train sitting at a station
        whose from_station code is the origin of segment N reports position N.
        """
        code = str(station_code).strip().upper()

        route = engine._get_train_route(train_number)

        matches = route[route["from_station"].astype(str).str.strip().str.upper() == code]

        if not matches.empty:
            return int(matches["route_order"].min())

        max_order = int(route["route_order"].max())
        to_station_exists = (route["to_station"].astype(str).str.strip().str.upper() == code).any()
        if to_station_exists:
            return max_order + 1

        raise SIHETANotCovered(
            f"Train {train_number} is in the SIH route dataset but station "
            f"{station_code} is not on its route"
        )

    def _build_train_state(self, train_number, position, station_code, route_position):
        from train_state import TrainState

        delay = float(max(position.delay_minutes, 0))
        now = position.timestamp if position.timestamp else datetime.now(timezone.utc)

        return TrainState(
            train_number=str(train_number).strip().lstrip("0"),
            current_station=station_code,
            current_route_position=route_position,
            current_arrival_delay=delay,
            current_departure_delay=delay,
            current_time=now,
        )

    # ------------------------------------------------------------------
    # Response building
    # ------------------------------------------------------------------

    def _build_response(
        self,
        train_number,
        train_name,
        station_name,
        state,
        results,
        position_source,
    ) -> Dict[str, Any]:
        from eta_confidence import ETAConfidence
        from delay_impact import DelayImpactAnalyzer

        current_delay = max(float(state.current_departure_delay), float(state.current_arrival_delay))

        upcoming = []
        for item in results:
            upcoming.append({
                "station_code": item["target_station"],
                "station_name": item["target_station_name"],
                "route_position": int(item["target_route_position"]),
                "scheduled_remaining_minutes": round(float(item["scheduled_remaining_minutes"]), 2),
                "predicted_remaining_minutes": round(float(item["predicted_remaining_minutes"]), 2),
                "predicted_arrival_delay_minutes": round(float(item["predicted_future_arrival_delay"]), 2),
                "predicted_eta": item["eta"].isoformat(),
            })

        if results:
            final = results[-1]
            destination_station = final["target_station"]
            destination_station_name = final["target_station_name"]
            final_remaining = float(final["predicted_remaining_minutes"])
            final_delay = float(final["predicted_future_arrival_delay"])
            predicted_arrival_time = final["eta"]
        else:
            destination_station = str(state.current_station)
            destination_station_name = station_name or state.current_station
            final_remaining = 0.0
            final_delay = current_delay
            predicted_arrival_time = state.current_time if state.current_time else datetime.now(timezone.utc)

        stations_ahead = len(results)

        confidence = ETAConfidence().calculate(final_remaining, stations_ahead, current_delay)
        impact = DelayImpactAnalyzer().analyze(current_delay, final_delay, stations_ahead)

        return {
            "train_number": train_number,
            "train_name": train_name,
            "current_station": str(state.current_station),
            "current_station_name": station_name,
            "current_route_position": int(state.current_route_position),
            "current_delay_minutes": round(current_delay, 2),
            "current_time": state.current_time.isoformat() if state.current_time else None,
            "destination_station": destination_station,
            "destination_station_name": destination_station_name,
            "predicted_arrival_delay_minutes": round(final_delay, 2),
            "predicted_arrival_time": predicted_arrival_time.isoformat(),
            "predicted_remaining_minutes": round(final_remaining, 2),
            "upcoming_station_count": len(upcoming),
            "upcoming_stations": upcoming,
            "confidence_score": float(confidence["confidence_score"]),
            "confidence_level": confidence["confidence_level"],
            "impact_severity": impact["severity"],
            "delay_trend": impact["trend"],
            "route_impact": impact["route_impact"],
            "model_type": "SIH_ETA_CORE",
            "model_version": "STAGE13-LGBM",
            "data_source": DataSource.SIH_ETA_CORE if hasattr(DataSource, "SIH_ETA_CORE") else "SIH_ETA_CORE",
            "position_source": position_source,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }