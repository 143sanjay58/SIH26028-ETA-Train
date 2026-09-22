from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.train import Train, TrainPosition, TrainSchedule, TrainStatus
from backend.app.models.station import Station
from backend.app.models.route import Route, RouteSection
from backend.app.models.prediction import Prediction, PredictionExplanation, PredictionModelType
from backend.app.models.weather import WeatherObservation, WeatherSeverity
from backend.app.models.congestion import CongestionState, CongestionLevel
from backend.app.services.train_service import TrainService
from backend.app.services.station_service import StationService
from backend.app.services.weather_service import WeatherService
from backend.app.services.ai import ai_service
from backend.app.ml.predictor import ETAPredictor
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class ETAService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.train_service = TrainService(db)
        self.station_service = StationService(db)
        self.weather_service = WeatherService(db)
        self.predictor = ETAPredictor()

    async def predict_eta(
        self,
        train_number: str,
        include_explanations: bool = True,
        include_uncertainty: bool = True,
    ) -> Dict[str, Any]:
        train = await self.train_service.get_train_by_number(train_number)
        if not train:
            raise ValueError(f"Train {train_number} not found")

        position = await self.train_service.get_latest_position(train.id)
        if not position:
            raise ValueError(f"No position data for train {train_number}")

        upcoming = await self.train_service.get_upcoming_stations(train.id, limit=10)
        if not upcoming:
            baseline = self._baseline_prediction(train, position, None)
            return {
                **baseline,
                "confidence_score": baseline.get("confidence"),
                "prediction_interval_lower": None,
                "prediction_interval_upper": None,
                "explanations": [],
                "ai_explanation": None,
            }

        next_station_schedule = upcoming[0]
        next_station = next_station_schedule.station

        baseline = self._baseline_prediction(train, position, next_station)
        statistical = await self._statistical_prediction(train, position, next_station, upcoming)
        ml = await self._ml_prediction(train, position, next_station, upcoming)

        best = self._select_best_prediction(baseline, statistical, ml)

        explanations = []
        ai_explanation = None
        if include_explanations:
            explanations = self._generate_explanations(train, position, next_station, best)
            ai_explanation = await self._generate_ai_explanation(
                train, position, next_station, best, explanations
            )

        uncertainty = None
        if include_uncertainty:
            uncertainty = self._calculate_uncertainty(baseline, statistical, ml)

        await self._save_prediction(train.id, next_station.id, best, explanations)

        return {
            "train_number": train.train_number,
            "train_name": train.train_name,
            "current_station": position.current_station.name if position.current_station else None,
            "next_station": next_station.name if next_station else None,
            "destination_station": train.destination_station.name,
            "current_delay_minutes": position.delay_minutes,
            "predicted_arrival_delay_minutes": best["arrival_delay"],
            "predicted_arrival_time": best["arrival_time"],
            "prediction_interval_lower": uncertainty.get("lower") if uncertainty else None,
            "prediction_interval_upper": uncertainty.get("upper") if uncertainty else None,
            "confidence_score": best.get("confidence"),
            "model_type": best["model_type"],
            "model_version": best.get("model_version", "1.0"),
            "explanations": explanations,
            "ai_explanation": ai_explanation,
            "data_source": position.source,
            "generated_at": datetime.now(timezone.utc),
        }

    def _baseline_prediction(
        self, train: Train, position: TrainPosition, next_station: Optional[Station]
    ) -> Dict[str, Any]:
        scheduled_arrival = train.scheduled_arrival
        current_delay = position.delay_minutes

        return {
            "model_type": PredictionModelType.BASELINE,
            "arrival_delay": current_delay,
            "arrival_time": scheduled_arrival + timedelta(minutes=current_delay) if scheduled_arrival else None,
            "confidence": 0.5,
            "train_number": train.train_number,
            "train_name": train.train_name,
            "current_station": position.current_station.name if position.current_station else None,
            "next_station": next_station.name if next_station else None,
            "destination_station": train.destination_station.name,
            "current_delay_minutes": position.delay_minutes,
            "predicted_arrival_delay_minutes": current_delay,
            "predicted_arrival_time": scheduled_arrival + timedelta(minutes=current_delay) if scheduled_arrival else None,
            "model_version": "1.0",
            "data_source": position.source,
            "generated_at": datetime.now(timezone.utc),
        }

    async def _statistical_prediction(
        self,
        train: Train,
        position: TrainPosition,
        next_station: Optional[Station],
        upcoming: List[TrainSchedule],
    ) -> Dict[str, Any]:
        if not next_station:
            return self._baseline_prediction(train, position, None)

        section_result = await self.db.execute(
            select(RouteSection)
            .where(
                and_(
                    RouteSection.route_id == train.route_id,
                    RouteSection.from_station_id == position.current_station_id,
                    RouteSection.to_station_id == next_station.id,
                )
            )
        )
        section = section_result.scalar_one_or_none()

        if not section or not section.historical_avg_time_minutes:
            return self._baseline_prediction(train, position, next_station)

        current_speed = max(position.speed_kmh, 1.0)
        distance_to_next = position.distance_to_next_km or section.distance_km
        estimated_time = (distance_to_next / current_speed) * 60

        historical_avg = section.historical_avg_time_minutes
        delay_factor = 1.0 + (position.delay_minutes / 60.0) if position.delay_minutes > 0 else 1.0
        predicted_time = historical_avg * delay_factor

        final_time = (estimated_time + predicted_time) / 2
        arrival_delay = final_time - section.scheduled_travel_time_minutes

        station_schedule = await self._get_station_schedule(train.id, next_station.id)
        scheduled = station_schedule.scheduled_arrival if station_schedule else train.scheduled_arrival
        predicted_arrival = scheduled + timedelta(minutes=arrival_delay) if scheduled else None

        return {
            "model_type": PredictionModelType.STATISTICAL,
            "arrival_delay": max(0, arrival_delay),
            "arrival_time": predicted_arrival,
            "confidence": 0.7,
        }

    async def _ml_prediction(
        self,
        train: Train,
        position: TrainPosition,
        next_station: Optional[Station],
        upcoming: List[TrainSchedule],
    ) -> Dict[str, Any]:
        features = await self._build_features(train, position, next_station, upcoming)
        if not features:
            return self._baseline_prediction(train, position, next_station)

        try:
            result = await self.predictor.predict(features)
            arrival_delay = result.get("delay_minutes", position.delay_minutes)
            confidence = result.get("confidence", 0.8)

            station_schedule = await self._get_station_schedule(train.id, next_station.id)
            scheduled = station_schedule.scheduled_arrival if station_schedule else train.scheduled_arrival
            predicted_arrival = scheduled + timedelta(minutes=arrival_delay) if scheduled else None

            return {
                "model_type": PredictionModelType.ML,
                "arrival_delay": arrival_delay,
                "arrival_time": predicted_arrival,
                "confidence": confidence,
                "model_version": result.get("model_version", "1.0"),
            }
        except Exception as e:
            logger.error("ML prediction failed", error=str(e))
            return self._baseline_prediction(train, position, next_station)

    def _select_best_prediction(
        self, baseline: Dict, statistical: Dict, ml: Dict
    ) -> Dict:
        if ml.get("confidence", 0) > 0.7:
            return ml
        if statistical.get("confidence", 0) > 0.6:
            return statistical
        return baseline

    async def _build_features(
        self,
        train: Train,
        position: TrainPosition,
        next_station: Optional[Station],
        upcoming: List[TrainSchedule],
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)

        section_result = await self.db.execute(
            select(RouteSection)
            .where(
                and_(
                    RouteSection.route_id == train.route_id,
                    RouteSection.from_station_id == position.current_station_id,
                    RouteSection.to_station_id == next_station.id if next_station else None,
                )
            )
        )
        section = section_result.scalar_one_or_none()

        weather = await self.weather_service.get_current_weather(
            position.latitude, position.longitude
        )

        congestion = None
        if section:
            congestion_result = await self.db.execute(
                select(CongestionState)
                .where(CongestionState.section_id == section.id)
                .order_by(desc(CongestionState.measured_at))
                .limit(1)
            )
            congestion = congestion_result.scalar_one_or_none()

        features = {
            "train_type": train.train_type.value,
            "hour": now.hour,
            "day_of_week": now.weekday(),
            "month": now.month,
            "is_peak": 1 if now.hour in [7, 8, 9, 17, 18, 19] else 0,
            "current_speed": position.speed_kmh,
            "avg_speed": await self._calculate_avg_speed(train.id),
            "current_delay": position.delay_minutes,
            "delay_trend": await self._calculate_delay_trend(train.id),
            "section_distance": section.distance_km if section else 0,
            "section_historical_avg": section.historical_avg_time_minutes if section else 0,
            "section_historical_delay_prob": section.historical_delay_probability if section else 0,
            "station_dwell": (await self._get_station_schedule(train.id, next_station.id)).scheduled_dwell_minutes if next_station else 2,
            "is_junction": 1 if next_station and next_station.is_junction else 0,
            "nearby_trains": congestion.train_count if congestion else 0,
            "congestion_level": self._congestion_to_numeric(congestion.level if congestion else CongestionLevel.LOW),
            "preceding_train_delay": congestion.preceding_train_delay_minutes if congestion else 0,
            "temperature": weather.temperature_celsius if weather else 25,
            "humidity": weather.humidity_percent if weather else 50,
            "wind_speed": weather.wind_speed_kmh if weather else 0,
            "visibility": weather.visibility_km if weather else 10,
            "precipitation": weather.precipitation_mm if weather else 0,
            "weather_severity": self._weather_severity_to_numeric(weather.severity if weather else WeatherSeverity.NORMAL),
        }
        return features

    def _generate_explanations(
        self,
        train: Train,
        position: TrainPosition,
        next_station: Optional[Station],
        prediction: Dict,
    ) -> List[Dict[str, Any]]:
        explanations = []

        if position.delay_minutes > 0:
            explanations.append({
                "factor_name": "Current Delay",
                "factor_value": position.delay_minutes,
                "contribution_minutes": position.delay_minutes,
                "direction": "POSITIVE",
                "description": f"Train is currently {position.delay_minutes} minutes behind schedule",
            })

        if prediction.get("congestion_contribution", 0) > 0:
            explanations.append({
                "factor_name": "Congestion",
                "factor_value": prediction["congestion_contribution"],
                "contribution_minutes": prediction["congestion_contribution"],
                "direction": "POSITIVE",
                "description": f"Section congestion adding {prediction['congestion_contribution']:.0f} minutes delay",
            })

        if prediction.get("weather_contribution", 0) > 0:
            explanations.append({
                "factor_name": "Weather",
                "factor_value": prediction["weather_contribution"],
                "contribution_minutes": prediction["weather_contribution"],
                "direction": "POSITIVE",
                "description": f"Adverse weather conditions adding delay",
            })

        if prediction.get("recovery_contribution", 0) < 0:
            explanations.append({
                "factor_name": "Recovery",
                "factor_value": abs(prediction["recovery_contribution"]),
                "contribution_minutes": prediction["recovery_contribution"],
                "direction": "NEGATIVE",
                "description": f"Train recovering {abs(prediction['recovery_contribution']):.0f} minutes",
            })

        return explanations

    async def _generate_ai_explanation(
        self,
        train: Train,
        position: TrainPosition,
        next_station: Optional[Station],
        prediction: Dict,
        explanations: List[Dict[str, Any]],
    ) -> Optional[str]:
        if not ai_service._providers:
            return None

        try:
            prompt = self._build_ai_prompt(train, position, next_station, prediction, explanations)
            system_prompt = (
                "You are a railway operations expert. Provide a clear, concise explanation "
                "of the ETA prediction for a train delay. Focus on the key factors contributing "
                "to the delay in simple language for passengers and operators."
            )
            
            response = await ai_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=300,
            )
            return response.content
        except Exception as e:
            logger.warning("AI explanation generation failed, using local explanations", error=str(e))
            return None

    def _build_ai_prompt(
        self,
        train: Train,
        position: TrainPosition,
        next_station: Optional[Station],
        prediction: Dict,
        explanations: List[Dict[str, Any]],
    ) -> str:
        delay = prediction.get("arrival_delay", 0)
        next_station_name = next_station.name if next_station else "destination"
        
        factor_descriptions = []
        for exp in explanations:
            factor_descriptions.append(
                f"- {exp['factor_name']}: {exp['description']}"
            )
        
        factors_text = "\n".join(factor_descriptions) if factor_descriptions else "No significant delay factors identified."
        
        return (
            f"Train {train.train_number} ({train.train_name}) is currently "
            f"{position.delay_minutes} minutes behind schedule. "
            f"Next station: {next_station_name}. "
            f"Predicted arrival delay: {delay} minutes.\n\n"
            f"Contributing factors:\n{factors_text}\n\n"
            f"Provide a brief passenger-friendly explanation (2-3 sentences)."
        )

    def _calculate_uncertainty(
        self, baseline: Dict, statistical: Dict, ml: Dict
    ) -> Dict[str, datetime]:
        delays = [baseline.get("arrival_delay", 0), statistical.get("arrival_delay", 0), ml.get("arrival_delay", 0)]
        mean_delay = sum(delays) / len(delays)
        std_delay = (sum((d - mean_delay) ** 2 for d in delays) / len(delays)) ** 0.5

        base_time = ml.get("arrival_time") or statistical.get("arrival_time") or baseline.get("arrival_time")
        if not base_time:
            return {}

        margin = max(5, std_delay * 1.96)
        return {
            "lower": base_time - timedelta(minutes=margin),
            "upper": base_time + timedelta(minutes=margin),
        }

    async def _save_prediction(
        self,
        train_id: int,
        station_id: int,
        prediction: Dict,
        explanations: List[Dict],
    ):
        pred = Prediction(
            train_id=train_id,
            station_id=station_id,
            model_type=prediction["model_type"],
            model_version=prediction.get("model_version", "1.0"),
            predicted_arrival_delay_minutes=prediction.get("arrival_delay"),
            predicted_arrival_time=prediction.get("arrival_time"),
            confidence_score=prediction.get("confidence"),
            features={},
            prediction_time=datetime.now(timezone.utc),
            is_current=True,
        )
        self.db.add(pred)
        await self.db.flush()

        for exp in explanations:
            explanation = PredictionExplanation(
                prediction_id=pred.id,
                factor_name=exp["factor_name"],
                factor_value=exp["factor_value"],
                contribution_minutes=exp["contribution_minutes"],
                direction=exp["direction"],
                description=exp["description"],
            )
            self.db.add(explanation)

        await self.db.flush()

    async def _get_station_schedule(self, train_id: int, station_id: int) -> Optional[TrainSchedule]:
        from sqlalchemy import select
        result = await self.db.execute(
            select(TrainSchedule).where(
                and_(TrainSchedule.train_id == train_id, TrainSchedule.station_id == station_id)
            )
        )
        return result.scalar_one_or_none()

    async def _calculate_avg_speed(self, train_id: int) -> float:
        from sqlalchemy import select, func
        result = await self.db.execute(
            select(func.avg(TrainPosition.speed_kmh)).where(
                and_(TrainPosition.train_id == train_id, TrainPosition.speed_kmh > 0)
            )
        )
        return result.scalar() or 60.0

    async def _calculate_delay_trend(self, train_id: int) -> float:
        from sqlalchemy import select
        result = await self.db.execute(
            select(TrainPosition.delay_minutes)
            .where(TrainPosition.train_id == train_id)
            .order_by(TrainPosition.timestamp.desc())
            .limit(5)
        )
        delays = list(result.scalars().all())
        if len(delays) < 2:
            return 0.0
        return (delays[0] - delays[-1]) / len(delays)

    def _congestion_to_numeric(self, level: CongestionLevel) -> float:
        mapping = {
            CongestionLevel.LOW: 0.0,
            CongestionLevel.MEDIUM: 1.0,
            CongestionLevel.HIGH: 2.0,
            CongestionLevel.CRITICAL: 3.0,
        }
        return mapping.get(level, 0.0)

    def _weather_severity_to_numeric(self, severity: str) -> float:
        mapping = {
            WeatherSeverity.NORMAL: 0.0,
            WeatherSeverity.CAUTION: 1.0,
            WeatherSeverity.SEVERE: 2.0,
        }
        return mapping.get(severity, 0.0)