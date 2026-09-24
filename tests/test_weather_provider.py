from __future__ import annotations

from typing import Any

import httpx
import pytest

from services.api.weather_provider import OpenMeteoProvider, WeatherProviderError


def valid_payload() -> dict[str, Any]:
    return {
        "current": {
            "time": "2026-09-24T10:00",
            "temperature_2m": 29.5,
            "precipitation": 0.2,
            "rain": 0.2,
            "weather_code": 2,
        },
        "daily": {
            "time": ["2026-09-24", "2026-09-25"],
            "weather_code": [2, 3],
            "temperature_2m_max": [31.0, 30.0],
            "temperature_2m_min": [24.0, 23.5],
            "precipitation_sum": [1.0, 3.5],
        },
    }


class FakeClient:
    def __init__(self, body: dict[str, Any] | None = None, error: Exception | None = None):
        self.body = body if body is not None else valid_payload()
        self.error = error
        self.url = ""
        self.params: dict[str, Any] = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def get(self, url: str, params: dict[str, Any]):
        self.url = url
        self.params = params
        if self.error:
            raise self.error
        return httpx.Response(
            200,
            json=self.body,
            request=httpx.Request("GET", url, params=params),
        )


def install_fake_client(monkeypatch, fake: FakeClient):
    monkeypatch.setattr(httpx, "Client", lambda timeout: fake)


def test_open_meteo_reachability_and_forecast_use_local_units_and_attribution(monkeypatch):
    fake = FakeClient()
    install_fake_client(monkeypatch, fake)
    provider = OpenMeteoProvider()

    provider.check_reachable()
    report = provider.get_forecast(14.1, 121.3)

    assert fake.url.endswith("/v1/forecast")
    assert fake.params["timezone"] == "Asia/Manila"
    assert fake.params["temperature_unit"] == "celsius"
    assert fake.params["precipitation_unit"] == "mm"
    assert report["current"]["condition"] == "Partly cloudy"
    assert report["forecast"][0]["date"] == "2026-09-24"
    assert report["forecast"][1]["rain_mm"] == 3.5
    assert "CC BY 4.0" in report["attribution"]


@pytest.mark.parametrize(
    "error",
    [httpx.ReadTimeout("timed out"), httpx.ConnectError("offline")],
)
def test_open_meteo_network_errors_are_mapped(error, monkeypatch):
    fake = FakeClient(error=error)
    install_fake_client(monkeypatch, fake)
    provider = OpenMeteoProvider()

    with pytest.raises(WeatherProviderError) as raised:
        provider.check_reachable()

    assert raised.value.code in {"WEATHER_TIMEOUT", "WEATHER_UNAVAILABLE"}


@pytest.mark.parametrize(
    "mutate",
    [
        lambda body: body["current"].update(temperature_2m=None),
        lambda body: body["current"].update(weather_code="rain"),
        lambda body: body["daily"]["time"].append("2026-09-26"),
        lambda body: body["daily"]["time"].__setitem__(0, "not-a-date"),
        lambda body: body["daily"]["temperature_2m_max"].__setitem__(0, float("nan")),
    ],
)
def test_open_meteo_rejects_invalid_weather_shapes_and_values(monkeypatch, mutate):
    payload = valid_payload()
    mutate(payload)
    install_fake_client(monkeypatch, FakeClient(payload))

    with pytest.raises(WeatherProviderError, match="WEATHER_UNAVAILABLE"):
        OpenMeteoProvider().get_forecast(14.1, 121.3)
