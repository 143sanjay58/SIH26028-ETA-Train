from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.train import Train, TrainPosition
from backend.app.models.station import Station, StationEvent
from backend.app.models.route import RouteSection
from backend.app.models.alert import Alert, AlertType, AlertSeverity
from backend.app.models.congestion import CongestionState, CongestionLevel
from backend.app.models.weather import WeatherObservation, WeatherSeverity
from backend.app.services.train_service import TrainService
from backend.app.services.congestion_service import CongestionService
from backend.app.services.weather_service import WeatherService
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.train_service = TrainService(db)
        self.congestion_service = CongestionService(db)
        self.weather_service = WeatherService(db)

    async def generate_alerts_for_train(self, train_id: int) -> List[Alert]:
        alerts = []
        train = await self.train_service.get_train_by_id(train_id)
        if not train:
            return alerts

        position = await self.train_service.get_latest_position(train_id)
        if not position:
            return alerts

        alerts.extend(await self._check_destination_delay(train, position))
        alerts.extend(await self._check_congestion_alerts(train, position))
        alerts.extend(await self._check_extended_halt(train, position))
        alerts.extend(await self._check_weather_alerts(train, position))
        alerts.extend(await self._check_speed_anomaly(train, position))
        alerts.extend(await self._check_delay_propagation(train, position))
        alerts.extend(await self._check_recovery(train, position))

        for alert in alerts:
            self.db.add(alert)

        if alerts:
            await self.db.flush()

        return alerts

    async def _check_destination_delay(self, train: Train, position: TrainPosition) -> List[Alert]:
        if position.delay_minutes <= 10:
            return []

        severity = AlertSeverity.WARNING
        if position.delay_minutes > 30:
            severity = AlertSeverity.CRITICAL

        return [Alert(
            train_id=train.id,
            alert_type=AlertType.DESTINATION_DELAY,
            severity=severity,
            title=f"Train {train.train_number} delayed at destination",
            message=f"Current delay: {position.delay_minutes} minutes. Predicted arrival delay may exceed {position.delay_minutes} minutes.",
            predicted_impact_minutes=position.delay_minutes,
            confidence=0.8,
            alert_metadata={"current_delay": position.delay_minutes, "position_source": position.source},
        )]

    async def _check_congestion_alerts(self, train: Train, position: TrainPosition) -> List[Alert]:
        if not position.current_station_id:
            return []

        congestion_result = await self.db.execute(
            select(CongestionState)
            .where(CongestionState.station_id == position.current_station_id)
            .order_by(CongestionState.measured_at.desc())
            .limit(1)
        )
        congestion = congestion_result.scalar_one_or_none()

        if not congestion or congestion.level in [CongestionLevel.LOW, CongestionLevel.MEDIUM]:
            return []

        severity = AlertSeverity.WARNING if congestion.level == CongestionLevel.HIGH else AlertSeverity.CRITICAL

        return [Alert(
            train_id=train.id,
            station_id=position.current_station_id,
            alert_type=AlertType.HIGH_CONGESTION,
            severity=severity,
            title=f"High congestion at {position.current_station.name if position.current_station else 'station'}",
            message=f"Congestion level: {congestion.level}. {congestion.train_count} trains in area. Average delay: {congestion.avg_delay_minutes:.0f} min.",
            predicted_impact_minutes=int(congestion.avg_delay_minutes),
            confidence=0.75,
            alert_metadata={"congestion_level": congestion.level.value, "train_count": congestion.train_count},
        )]

    async def _check_extended_halt(self, train: Train, position: TrainPosition) -> List[Alert]:
        if not position.current_station_id or position.speed_kmh > 5:
            return []

        events_result = await self.db.execute(
            select(StationEvent)
            .where(
                and_(
                    StationEvent.train_id == train.id,
                    StationEvent.station_id == position.current_station_id,
                    StationEvent.is_extended_halt == True,
                )
            )
            .order_by(StationEvent.actual_time.desc())
            .limit(1)
        )
        event = events_result.scalar_one_or_none()

        if not event or not event.extended_minutes or event.extended_minutes < 10:
            return []

        return [Alert(
            train_id=train.id,
            station_id=position.current_station_id,
            alert_type=AlertType.EXTENDED_HALT,
            severity=AlertSeverity.WARNING,
            title=f"Extended halt detected for train {train.train_number}",
            message=f"Train halted for {event.dwell_minutes} minutes (expected: {event.expected_dwell_minutes} min). Additional delay: {event.extended_minutes} minutes.",
            predicted_impact_minutes=event.extended_minutes,
            confidence=0.9,
            alert_metadata={"extended_minutes": event.extended_minutes, "dwell_minutes": event.dwell_minutes},
        )]

    async def _check_weather_alerts(self, train: Train, position: TrainPosition) -> List[Alert]:
        weather = await self.weather_service.get_current_weather(position.latitude, position.longitude)
        if not weather or weather.severity == WeatherSeverity.NORMAL:
            return []

        severity = AlertSeverity.WARNING if weather.severity == WeatherSeverity.CAUTION else AlertSeverity.CRITICAL

        return [Alert(
            train_id=train.id,
            alert_type=AlertType.WEATHER_RISK,
            severity=severity,
            title=f"Weather risk for train {train.train_number}",
            message=f"Current conditions: {weather.weather_description}. Temperature: {weather.temperature_celsius}°C, Wind: {weather.wind_speed_kmh} km/h, Visibility: {weather.visibility_km} km.",
            confidence=0.7,
            alert_metadata={
                "weather_condition": weather.weather_condition,
                "severity": weather.severity,
                "temperature": weather.temperature_celsius,
                "wind_speed": weather.wind_speed_kmh,
                "visibility": weather.visibility_km,
            },
        )]

    async def _check_speed_anomaly(self, train: Train, position: TrainPosition) -> List[Alert]:
        recent_positions = await self.train_service.get_positions(train.id, limit=10)
        if len(recent_positions) < 3:
            return []

        speeds = [p.speed_kmh for p in recent_positions if p.speed_kmh > 0]
        if len(speeds) < 3:
            return []

        avg_speed = sum(speeds) / len(speeds)
        current_speed = position.speed_kmh

        if current_speed > 0 and avg_speed > 0:
            drop_pct = (avg_speed - current_speed) / avg_speed * 100
            if drop_pct > 50 and current_speed < 30:
                return [Alert(
                    train_id=train.id,
                    alert_type=AlertType.SPEED_ANOMALY,
                    severity=AlertSeverity.WARNING,
                    title=f"Speed anomaly detected for train {train.train_number}",
                    message=f"Speed dropped {drop_pct:.0f}% from average ({avg_speed:.0f} → {current_speed:.0f} km/h). Possible signal wait or obstruction.",
                    confidence=0.75,
                    alert_metadata={"avg_speed": avg_speed, "current_speed": current_speed, "drop_percentage": drop_pct},
                )]

        return []

    async def _check_delay_propagation(self, train: Train, position: TrainPosition) -> List[Alert]:
        if position.delay_minutes <= 15:
            return []

        upcoming = await self.train_service.get_upcoming_stations(train.id, limit=5)
        if not upcoming:
            return []

        propagated_delay = position.delay_minutes
        impacts = []

        for i, schedule in enumerate(upcoming):
            section_result = await self.db.execute(
                select(RouteSection)
                .where(
                    and_(
                        RouteSection.route_id == train.route_id,
                        RouteSection.from_station_id == (position.current_station_id if i == 0 else upcoming[i-1].station_id),
                        RouteSection.to_station_id == schedule.station_id,
                    )
                )
            )
            section = section_result.scalar_one_or_none()

            if section and section.historical_recovery_minutes:
                recovery = min(section.historical_recovery_minutes, propagated_delay * 0.3)
                propagated_delay -= recovery
                impacts.append({"station": schedule.station.name, "recovery": recovery, "remaining_delay": propagated_delay})
            else:
                impacts.append({"station": schedule.station.name, "recovery": 0, "remaining_delay": propagated_delay})

        if propagated_delay > position.delay_minutes * 0.5:
            return [Alert(
                train_id=train.id,
                alert_type=AlertType.DELAY_PROPAGATION,
                severity=AlertSeverity.WARNING,
                title=f"Delay propagation for train {train.train_number}",
                message=f"Current delay of {position.delay_minutes} min may propagate to destination. Projected delay at destination: {propagated_delay:.0f} min.",
                predicted_impact_minutes=int(propagated_delay),
                confidence=0.7,
                alert_metadata={"current_delay": position.delay_minutes, "projected_delay": propagated_delay, "impacts": impacts},
            )]

        return []

    async def _check_recovery(self, train: Train, position: TrainPosition) -> List[Alert]:
        recent_positions = await self.train_service.get_positions(train.id, limit=5)
        if len(recent_positions) < 2:
            return []

        prev_delay = recent_positions[1].delay_minutes
        curr_delay = position.delay_minutes

        if prev_delay > curr_delay + 5:
            return [Alert(
                train_id=train.id,
                alert_type=AlertType.TRAIN_RECOVERY,
                severity=AlertSeverity.INFO,
                title=f"Train {train.train_number} recovering delay",
                message=f"Delay reduced from {prev_delay} to {curr_delay} minutes. Recovery of {prev_delay - curr_delay} minutes detected.",
                confidence=0.8,
                alert_metadata={"previous_delay": prev_delay, "current_delay": curr_delay, "recovery": prev_delay - curr_delay},
            )]

        return []

    async def get_active_alerts(
        self,
        train_id: Optional[int] = None,
        station_id: Optional[int] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        query = select(Alert).where(Alert.is_active == True)

        if train_id:
            query = query.where(Alert.train_id == train_id)
        if station_id:
            query = query.where(Alert.station_id == station_id)
        if severity:
            query = query.where(Alert.severity == severity)

        query = query.order_by(Alert.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def acknowledge_alert(self, alert_id: int, user_id: int) -> Optional[Alert]:
        alert = await self.db.get(Alert, alert_id)
        if not alert:
            return None

        alert.is_acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        await self.db.flush()
        return alert

    async def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        alert = await self.db.get(Alert, alert_id)
        if not alert:
            return None

        alert.is_active = False
        alert.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        return alert