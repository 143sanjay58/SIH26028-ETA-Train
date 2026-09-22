import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import httpx
import os

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.weather import WeatherObservation, WeatherForecast, WeatherSeverity
from backend.app.models.station import Station
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class WeatherService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = httpx.AsyncClient(timeout=10.0)
        self.cache: dict = {}
        self.cache_ttl = 300

    async def close(self):
        await self.client.aclose()

    async def get_current_weather(
        self, latitude: float, longitude: float, station_id: Optional[int] = None
    ) -> Optional[WeatherObservation]:
        cache_key = f"weather:{latitude}:{longitude}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now(timezone.utc) - cached_time).total_seconds() < self.cache_ttl:
                logger.debug("Weather cache hit", key=cache_key)
                return cached_data

        weather = await self._fetch_weather(latitude, longitude)
        if weather:
            weather.station_id = station_id
            self.cache[cache_key] = (weather, datetime.now(timezone.utc))
            await self._save_observation(weather)
        return weather

    async def _fetch_weather(self, latitude: float, longitude: float) -> Optional[WeatherObservation]:
        if settings.weather_provider == "open-meteo":
            return await self._fetch_open_meteo(latitude, longitude)
        elif settings.weather_provider == "openweathermap" and settings.weather_api_key:
            return await self._fetch_openweathermap(latitude, longitude)
        return await self._fetch_open_meteo(latitude, longitude)

    async def _fetch_open_meteo(self, latitude: float, longitude: float) -> Optional[WeatherObservation]:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,cloud_cover,precipitation,weather_code",
                "timezone": "UTC",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})

            return self._parse_open_meteo_current(current, latitude, longitude)
        except Exception as e:
            logger.error("Open-Meteo API error", error=str(e))
            return None

    async def _fetch_openweathermap(self, latitude: float, longitude: float) -> Optional[WeatherObservation]:
        if not settings.weather_api_key:
            return None
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": settings.weather_api_key,
                "units": "metric",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return self._parse_openweathermap(data, latitude, longitude)
        except Exception as e:
            logger.error("OpenWeatherMap API error", error=str(e))
            return None

    def _parse_open_meteo_current(self, current: dict, latitude: float, longitude: float) -> WeatherObservation:
        weather_code = current.get("weather_code", 0)
        condition, description, severity = self._decode_weather_code(weather_code)

        return WeatherObservation(
            latitude=latitude,
            longitude=longitude,
            temperature_celsius=current.get("temperature_2m", 0),
            feels_like_celsius=current.get("apparent_temperature"),
            humidity_percent=current.get("relative_humidity_2m", 0),
            pressure_hpa=current.get("pressure_msl"),
            wind_speed_kmh=current.get("wind_speed_10m", 0) * 3.6,
            wind_direction_degrees=current.get("wind_direction_10m"),
            wind_gust_kmh=current.get("wind_gusts_10m", 0) * 3.6 if current.get("wind_gusts_10m") else None,
            visibility_km=current.get("visibility", 0) / 1000 if current.get("visibility") else None,
            cloud_cover_percent=current.get("cloud_cover"),
            weather_condition=condition,
            weather_description=description,
            precipitation_mm=current.get("precipitation"),
            precipitation_probability=None,
            severity=severity,
            observed_at=self._parse_iso(current.get("time", datetime.now(timezone.utc).isoformat())),
            source="OPEN_METEO",
            raw_data=current,
        )

    def _parse_openweathermap(self, data: dict, latitude: float, longitude: float) -> WeatherObservation:
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = data.get("weather", [{}])[0]

        condition = weather.get("main", "Clear")
        description = weather.get("description", condition)
        severity = self._assess_severity(condition, main.get("humidity", 0), wind.get("speed", 0) * 3.6)

        return WeatherObservation(
            latitude=latitude,
            longitude=longitude,
            temperature_celsius=main.get("temp", 0),
            feels_like_celsius=main.get("feels_like"),
            humidity_percent=main.get("humidity", 0),
            pressure_hpa=main.get("pressure"),
            wind_speed_kmh=wind.get("speed", 0) * 3.6,
            wind_direction_degrees=wind.get("deg"),
            wind_gust_kmh=wind.get("gust", 0) * 3.6 if wind.get("gust") else None,
            visibility_km=data.get("visibility", 0) / 1000 if data.get("visibility") else None,
            cloud_cover_percent=data.get("clouds", {}).get("all"),
            weather_condition=condition,
            weather_description=description,
            weather_icon=weather.get("icon"),
            precipitation_mm=data.get("rain", {}).get("1h") or data.get("snow", {}).get("1h"),
            precipitation_probability=data.get("pop", 0) * 100 if data.get("pop") else None,
            severity=severity,
            observed_at=datetime.fromtimestamp(data.get("dt", 0), tz=timezone.utc),
            source="OPENWEATHERMAP",
            raw_data=data,
        )

    def _parse_iso(self, time_str: str) -> datetime:
        parsed = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _decode_weather_code(self, code: int) -> tuple[str, str, str]:
        codes = {
            0: ("Clear", "Clear sky", WeatherSeverity.NORMAL),
            1: ("MainlyClear", "Mainly clear", WeatherSeverity.NORMAL),
            2: ("PartlyCloudy", "Partly cloudy", WeatherSeverity.NORMAL),
            3: ("Overcast", "Overcast", WeatherSeverity.NORMAL),
            45: ("Fog", "Fog", WeatherSeverity.CAUTION),
            48: ("Fog", "Depositing rime fog", WeatherSeverity.CAUTION),
            51: ("Drizzle", "Light drizzle", WeatherSeverity.CAUTION),
            53: ("Drizzle", "Moderate drizzle", WeatherSeverity.CAUTION),
            55: ("Drizzle", "Dense drizzle", WeatherSeverity.CAUTION),
            56: ("FreezingDrizzle", "Light freezing drizzle", WeatherSeverity.SEVERE),
            57: ("FreezingDrizzle", "Dense freezing drizzle", WeatherSeverity.SEVERE),
            61: ("Rain", "Slight rain", WeatherSeverity.CAUTION),
            63: ("Rain", "Moderate rain", WeatherSeverity.CAUTION),
            65: ("Rain", "Heavy rain", WeatherSeverity.SEVERE),
            66: ("FreezingRain", "Light freezing rain", WeatherSeverity.SEVERE),
            67: ("FreezingRain", "Heavy freezing rain", WeatherSeverity.SEVERE),
            71: ("Snow", "Slight snow fall", WeatherSeverity.CAUTION),
            73: ("Snow", "Moderate snow fall", WeatherSeverity.SEVERE),
            75: ("Snow", "Heavy snow fall", WeatherSeverity.SEVERE),
            77: ("SnowGrains", "Snow grains", WeatherSeverity.CAUTION),
            80: ("RainShowers", "Slight rain showers", WeatherSeverity.CAUTION),
            81: ("RainShowers", "Moderate rain showers", WeatherSeverity.CAUTION),
            82: ("RainShowers", "Violent rain showers", WeatherSeverity.SEVERE),
            85: ("SnowShowers", "Slight snow showers", WeatherSeverity.CAUTION),
            86: ("SnowShowers", "Heavy snow showers", WeatherSeverity.SEVERE),
            95: ("Thunderstorm", "Thunderstorm", WeatherSeverity.SEVERE),
            96: ("Thunderstorm", "Thunderstorm with slight hail", WeatherSeverity.SEVERE),
            99: ("Thunderstorm", "Thunderstorm with heavy hail", WeatherSeverity.SEVERE),
        }
        return codes.get(code, ("Unknown", "Unknown weather", WeatherSeverity.NORMAL))

    def _assess_severity(self, condition: str, humidity: int, wind_kmh: float) -> str:
        severe_conditions = ["Thunderstorm", "Tornado", "Hurricane", "Squall"]
        caution_conditions = ["Rain", "Drizzle", "Snow", "Fog", "Mist", "Haze", "Smoke", "Dust", "Sand"]

        if condition in severe_conditions:
            return WeatherSeverity.SEVERE
        if condition in caution_conditions:
            if humidity > 90 or wind_kmh > 50:
                return WeatherSeverity.SEVERE
            return WeatherSeverity.CAUTION
        return WeatherSeverity.NORMAL

    async def _save_observation(self, observation: WeatherObservation):
        if observation.station_id is None:
            return
        nested = await self.db.begin_nested()
        try:
            self.db.add(observation)
            await nested.commit()
        except Exception as e:
            logger.error("Failed to save weather observation", error=str(e))
            await nested.rollback()

    async def get_forecast(
        self, latitude: float, longitude: float, station_id: Optional[int] = None, days: int = 3
    ) -> List[WeatherForecast]:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,cloud_cover,precipitation,precipitation_probability,weather_code",
                "timezone": "UTC",
                "forecast_days": days,
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            hourly = data.get("hourly", {})

            forecasts = []
            times = hourly.get("time", [])
            for i, time_str in enumerate(times):
                forecast_time = self._parse_iso(time_str)
                if forecast_time < datetime.now(timezone.utc):
                    continue

                current_data = {k: v[i] for k, v in hourly.items() if isinstance(v, list) and i < len(v)}
                condition, description, severity = self._decode_weather_code(current_data.get("weather_code", 0))

                forecast = WeatherForecast(
                    station_id=station_id,
                    latitude=latitude,
                    longitude=longitude,
                    forecast_time=forecast_time,
                    valid_from=forecast_time,
                    valid_to=forecast_time + timedelta(hours=1),
                    temperature_celsius=current_data.get("temperature_2m", 0),
                    feels_like_celsius=current_data.get("apparent_temperature"),
                    humidity_percent=current_data.get("relative_humidity_2m", 0),
                    pressure_hpa=current_data.get("pressure_msl"),
                    wind_speed_kmh=current_data.get("wind_speed_10m", 0) * 3.6,
                    wind_direction_degrees=current_data.get("wind_direction_10m"),
                    wind_gust_kmh=current_data.get("wind_gusts_10m", 0) * 3.6 if current_data.get("wind_gusts_10m") else None,
                    visibility_km=current_data.get("visibility", 0) / 1000 if current_data.get("visibility") else None,
                    cloud_cover_percent=current_data.get("cloud_cover"),
                    weather_condition=condition,
                    weather_description=description,
                    precipitation_mm=current_data.get("precipitation"),
                    precipitation_probability=current_data.get("precipitation_probability"),
                    severity=severity,
                    source="OPEN_METEO",
                    raw_data=current_data,
                )
                forecasts.append(forecast)
                if station_id is not None:
                    self.db.add(forecast)

            if station_id is not None:
                nested = await self.db.begin_nested()
                try:
                    await nested.commit()
                except Exception as e:
                    logger.error("Failed to save weather forecast", error=str(e))
                    await nested.rollback()
            return forecasts
        except Exception as e:
            logger.error("Failed to fetch weather forecast", error=str(e))
            return []

    async def get_station_weather(self, station: Station) -> Optional[WeatherObservation]:
        return await self.get_current_weather(station.latitude, station.longitude, station.id)

    async def get_route_weather(self, stations: List[Station]) -> List[WeatherObservation]:
        results = []
        for station in stations[:5]:
            weather = await self.get_station_weather(station)
            if weather:
                results.append(weather)
        return results