import time
import httpx
from astrobot_mcp.config import (
    ASTROSPHERIC_API_KEY,
    ASTROSPHERIC_BASE_URL,
    DEFAULT_LAT,
    DEFAULT_LON,
    FORECAST_CACHE_TTL,
)

_forecast_cache: dict[str, tuple[float, dict]] = {}


def _cache_key(lat: float, lon: float) -> str:
    return f"{lat:.2f},{lon:.2f}"


async def get_forecast(
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get 81-hour astrophotography weather forecast from Astrospheric.

    Returns cloud cover, seeing, transparency, temperature, dew point, and wind
    forecasts. Costs 5 API credits per call (100/day limit), so results are
    cached for 1 hour.

    Args:
        latitude: Observer latitude (default: home location 35.65N)
        longitude: Observer longitude (default: home location 78.73W)
    """
    lat = latitude or DEFAULT_LAT
    lon = longitude or DEFAULT_LON
    key = _cache_key(lat, lon)

    if key in _forecast_cache:
        cached_time, cached_data = _forecast_cache[key]
        if time.time() - cached_time < FORECAST_CACHE_TTL:
            return {**cached_data, "_cached": True, "_cache_age_minutes": round((time.time() - cached_time) / 60)}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{ASTROSPHERIC_BASE_URL}/GetForecastData_V1",
            json={"Latitude": lat, "Longitude": lon, "APIKey": ASTROSPHERIC_API_KEY},
        )
        resp.raise_for_status()
        data = resp.json()

    _forecast_cache[key] = (time.time(), data)
    return data


async def get_sky(
    latitude: float | None = None,
    longitude: float | None = None,
    timestamp_ms: int | None = None,
) -> dict:
    """Get current sky object positions from Astrospheric.

    Returns positions of bright stars (mag < 5), all planets, Moon (with phase
    and illumination), and Sun. Costs 1 API credit per call.

    Args:
        latitude: Observer latitude (default: home location 35.65N)
        longitude: Observer longitude (default: home location 78.73W)
        timestamp_ms: Unix timestamp in milliseconds (default: now)
    """
    lat = latitude or DEFAULT_LAT
    lon = longitude or DEFAULT_LON
    ts = timestamp_ms or int(time.time() * 1000)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{ASTROSPHERIC_BASE_URL}/GetSky_V1",
            json={
                "Latitude": lat,
                "Longitude": lon,
                "MSSinceEpoch": ts,
                "APIKey": ASTROSPHERIC_API_KEY,
            },
        )
        resp.raise_for_status()
        return resp.json()
