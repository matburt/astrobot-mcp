import os
from datetime import datetime, timezone

from skyfield.api import load, wgs84, Star
from skyfield.almanac import moon_phase, fraction_illuminated

from astrobot_mcp.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_ELEVATION, SKYFIELD_DATA_DIR

os.makedirs(SKYFIELD_DATA_DIR, exist_ok=True)
_load = load
_load.directory = SKYFIELD_DATA_DIR

_ts = _load.timescale()
_eph = _load("de421.bsp")

BODIES = {
    "mercury": "mercury",
    "venus": "venus",
    "mars": "mars barycenter",
    "jupiter": "jupiter barycenter",
    "saturn": "saturn barycenter",
    "uranus": "uranus barycenter",
    "neptune": "neptune barycenter",
    "moon": "moon",
    "sun": "sun",
}


def _get_observer(lat: float | None, lon: float | None):
    return _eph["earth"] + wgs84.latlon(
        lat or DEFAULT_LAT,
        lon or DEFAULT_LON,
        elevation_m=DEFAULT_ELEVATION,
    )


def _to_skyfield_time(iso_time: str | None):
    if iso_time:
        dt = datetime.fromisoformat(iso_time)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return _ts.from_datetime(dt)
    return _ts.now()


def get_planet_position(
    body: str,
    time: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get the position of a solar system body (planet, Moon, or Sun).

    Returns altitude, azimuth, RA, Dec, distance, and constellation.

    Args:
        body: Planet name — "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "moon", or "sun"
        time: ISO 8601 datetime string (default: now). Example: "2026-03-31T22:00:00"
        latitude: Observer latitude (default: home location 35.65N)
        longitude: Observer longitude (default: home location 78.73W)
    """
    body_lower = body.lower()
    if body_lower not in BODIES:
        return {"error": f"Unknown body '{body}'. Valid: {list(BODIES.keys())}"}

    observer = _get_observer(latitude, longitude)
    t = _to_skyfield_time(time)
    target = _eph[BODIES[body_lower]]

    astrometric = observer.at(t).observe(target)
    apparent = astrometric.apparent()
    alt, az, _ = apparent.altaz()
    ra, dec, dist = apparent.radec()

    return {
        "body": body,
        "time_utc": t.utc_iso(),
        "altitude_deg": round(alt.degrees, 2),
        "azimuth_deg": round(az.degrees, 2),
        "ra": str(ra),
        "dec": str(dec),
        "distance_au": round(dist.au, 4),
        "is_above_horizon": bool(alt.degrees > 0),
    }


def get_moon_info(
    time: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get detailed Moon information including phase, illumination, and position.

    Args:
        time: ISO 8601 datetime string (default: now)
        latitude: Observer latitude (default: home location 35.65N)
        longitude: Observer longitude (default: home location 78.73W)
    """
    t = _to_skyfield_time(time)
    observer = _get_observer(latitude, longitude)

    moon = _eph["moon"]
    astrometric = observer.at(t).observe(moon)
    apparent = astrometric.apparent()
    alt, az, _ = apparent.altaz()
    ra, dec, dist = apparent.radec()

    phase_angle = moon_phase(_eph, t)
    illumination = fraction_illuminated(_eph, "moon", t)

    phase_deg = phase_angle.degrees
    if phase_deg < 45:
        phase_name = "New Moon"
    elif phase_deg < 90:
        phase_name = "Waxing Crescent"
    elif phase_deg < 135:
        phase_name = "First Quarter"
    elif phase_deg < 170:
        phase_name = "Waxing Gibbous"
    elif phase_deg < 190:
        phase_name = "Full Moon"
    elif phase_deg < 225:
        phase_name = "Waning Gibbous"
    elif phase_deg < 270:
        phase_name = "Last Quarter"
    elif phase_deg < 315:
        phase_name = "Waning Crescent"
    else:
        phase_name = "New Moon"

    return {
        "time_utc": t.utc_iso(),
        "phase_name": phase_name,
        "phase_angle_deg": round(phase_deg, 1),
        "illumination_pct": round(illumination * 100, 1),
        "altitude_deg": round(alt.degrees, 2),
        "azimuth_deg": round(az.degrees, 2),
        "ra": str(ra),
        "dec": str(dec),
        "distance_km": round(dist.km, 0),
        "is_above_horizon": bool(alt.degrees > 0),
    }
