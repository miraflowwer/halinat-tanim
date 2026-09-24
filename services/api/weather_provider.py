"""Open-Meteo adapter for live weather context."""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from typing import Any, Protocol

import httpx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_TIMEOUT_SECONDS = 5.0


class WeatherProviderError(Exception):
    def __init__(self, code: str, status_code: int = 503) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class WeatherProvider(Protocol):
    name: str

    def check_reachable(self) -> None: ...

    def get_forecast(self, latitude: float, longitude: float) -> dict[str, Any]: ...


def _condition_for_code(code: int) -> str:
    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Heavy drizzle",
        56: "Freezing drizzle",
        57: "Heavy freezing drizzle",
        61: "Light rain",
        63: "Rain",
        65: "Heavy rain",
        66: "Freezing rain",
        67: "Heavy freezing rain",
        71: "Light snow",
        73: "Snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Light rain showers",
        81: "Rain showers",
        82: "Heavy rain showers",
        85: "Light snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with light hail",
        99: "Thunderstorm with heavy hail",
    }
    return conditions.get(code, "Weather condition not available")


def _is_finite_number(value: Any) -> bool:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _is_weather_code(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class OpenMeteoProvider:
    name = "Open-Meteo"

    def __init__(self, timeout: float = WEATHER_TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    @staticmethod
    def _parameters(latitude: float, longitude: float) -> dict[str, str | int | float]:
        return {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,precipitation,rain,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "forecast_days": 3,
            "timezone": "Asia/Manila",
            "temperature_unit": "celsius",
            "precipitation_unit": "mm",
        }

    def _request(self, latitude: float, longitude: float) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    FORECAST_URL,
                    params=self._parameters(latitude, longitude),
                )
                response.raise_for_status()
                body = response.json()
        except httpx.TimeoutException:
            raise WeatherProviderError("WEATHER_TIMEOUT", 504) from None
        except (httpx.HTTPError, ValueError):
            raise WeatherProviderError("WEATHER_UNAVAILABLE") from None
        if not isinstance(body, dict):
            raise WeatherProviderError("WEATHER_UNAVAILABLE")
        return body

    def check_reachable(self) -> None:
        body = self._request(14.5995, 120.9842)
        current = body.get("current")
        if not isinstance(current, dict) or not _is_finite_number(
            current.get("temperature_2m")
        ):
            raise WeatherProviderError("WEATHER_UNAVAILABLE")

    def get_forecast(self, latitude: float, longitude: float) -> dict[str, Any]:
        body = self._request(latitude, longitude)
        current = body.get("current")
        daily = body.get("daily")
        if not isinstance(current, dict) or not isinstance(daily, dict):
            raise WeatherProviderError("WEATHER_UNAVAILABLE")
        required_current = ("time", "temperature_2m", "precipitation", "rain", "weather_code")
        required_daily = (
            "time",
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        )
        if any(key not in current for key in required_current) or any(
            key not in daily for key in required_daily
        ):
            raise WeatherProviderError("WEATHER_UNAVAILABLE")

        daily_values = [daily[key] for key in required_daily]
        if not all(isinstance(values, list) for values in daily_values) or len(
            {len(values) for values in daily_values}
        ) != 1 or not daily_values[0]:
            raise WeatherProviderError("WEATHER_UNAVAILABLE")

        try:
            datetime.fromisoformat(current["time"])
        except (TypeError, ValueError):
            raise WeatherProviderError("WEATHER_UNAVAILABLE") from None
        if (
            not _is_finite_number(current["temperature_2m"])
            or not _is_finite_number(current["precipitation"])
            or not _is_finite_number(current["rain"])
            or not _is_weather_code(current["weather_code"])
        ):
            raise WeatherProviderError("WEATHER_UNAVAILABLE")

        forecast = []
        for values in zip(*daily_values, strict=True):
            day, code, low, high, rain = values
            try:
                date.fromisoformat(day)
            except (TypeError, ValueError):
                raise WeatherProviderError("WEATHER_UNAVAILABLE") from None
            if (
                not _is_weather_code(code)
                or not _is_finite_number(low)
                or not _is_finite_number(high)
                or not _is_finite_number(rain)
            ):
                raise WeatherProviderError("WEATHER_UNAVAILABLE")
            forecast.append(
                {
                    "date": day,
                    "weather_code": code,
                    "condition": _condition_for_code(code),
                    "temperature_min_c": low,
                    "temperature_max_c": high,
                    "rain_mm": rain,
                }
            )
        return {
            "observed_at": current["time"],
            "retrieved_at": datetime.now(UTC).isoformat(),
            "current": {
                "temperature_c": current["temperature_2m"],
                "precipitation_mm": current["precipitation"],
                "rain_mm": current["rain"],
                "weather_code": current["weather_code"],
                "condition": _condition_for_code(current["weather_code"]),
            },
            "forecast": forecast,
            "attribution": "Weather data from Open-Meteo, licensed under CC BY 4.0.",
        }
