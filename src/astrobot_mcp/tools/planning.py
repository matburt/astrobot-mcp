from datetime import datetime, timezone

import astropy.units as u
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time
from astroplan import Observer, FixedTarget, AltitudeConstraint, MoonSeparationConstraint
from astroplan import is_observable
from pyongc.ongc import get as ongc_get, listObjects

from astrobot_mcp.config import DEFAULT_LAT, DEFAULT_LON, DEFAULT_ELEVATION


def _get_observer(lat: float | None = None, lon: float | None = None) -> Observer:
    return Observer(
        location=EarthLocation.from_geodetic(
            lon or DEFAULT_LON,
            lat or DEFAULT_LAT,
            DEFAULT_ELEVATION * u.m,
        ),
        name="Home Observatory",
        timezone="US/Eastern",
    )


def _parse_time(iso_time: str | None) -> Time:
    if iso_time:
        dt = datetime.fromisoformat(iso_time)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return Time(dt)
    return Time.now()


def _dso_to_target(obj) -> FixedTarget | None:
    try:
        coords = obj.coords
        if coords is None:
            return None
        # coords is a numpy array [[ra_h, ra_m, ra_s], [dec_d, dec_m, dec_s]]
        ra_str = obj.ra
        dec_str = obj.dec
        if not ra_str or not dec_str:
            return None
        coord = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
        return FixedTarget(coord=coord, name=obj.name)
    except Exception:
        return None


def _resolve_target(name: str) -> FixedTarget | None:
    try:
        obj = ongc_get(name)
        if obj is not None:
            target = _dso_to_target(obj)
            if target is not None:
                return target
    except Exception:
        pass
    try:
        return FixedTarget.from_name(name)
    except Exception:
        return None


def get_rise_set_transit(
    target_name: str,
    date: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get rise, set, and transit times for a deep sky object or named target.

    Args:
        target_name: Object name (e.g. "M31", "NGC 7000", "Vega", "Sirius")
        date: ISO 8601 date or datetime (default: tonight). Example: "2026-03-31"
        latitude: Observer latitude (default: home location 35.65N)
        longitude: Observer longitude (default: home location 78.73W)
    """
    observer = _get_observer(lat=latitude, lon=longitude)
    t = _parse_time(date)

    target = _resolve_target(target_name)
    if not target:
        return {"error": f"Could not find '{target_name}' in DSO catalogs or star databases"}

    try:
        rise = observer.target_rise_time(t, target, which="next")
        transit = observer.target_meridian_transit_time(t, target, which="next")
        set_time = observer.target_set_time(t, target, which="next")

        transit_alt = observer.altaz(transit, target).alt.deg

        return {
            "target": target_name,
            "rise_utc": rise.iso if rise else "circumpolar",
            "transit_utc": transit.iso if transit else None,
            "set_utc": set_time.iso if set_time else "circumpolar",
            "transit_altitude_deg": round(transit_alt, 1),
            "is_circumpolar": rise is None or set_time is None,
        }
    except Exception as e:
        return {"target": target_name, "error": str(e)}


def whats_visible(
    date: str | None = None,
    min_altitude: float = 30.0,
    max_magnitude: float = 10.0,
    min_moon_separation: float = 30.0,
    object_type: str | None = None,
    limit: int = 20,
    latitude: float | None = None,
    longitude: float | None = None,
) -> list[dict]:
    """Find DSOs visible tonight that meet imaging constraints.

    Filters the catalog by magnitude and type, then checks which objects are
    observable from the given location with altitude and moon separation
    constraints. Results are sorted by transit altitude (best positioned first).

    Args:
        date: ISO 8601 date (default: tonight). Example: "2026-03-31"
        min_altitude: Minimum altitude in degrees (default: 30)
        max_magnitude: Maximum visual magnitude (default: 10.0, brighter objects only)
        min_moon_separation: Minimum degrees from Moon (default: 30)
        object_type: Filter by OpenNGC type code — "G", "OC", "GC", "PN", "HII", "EmN", "RfN", "SNR", etc.
        limit: Maximum results (default: 20)
        latitude: Observer latitude (default: home location 35.65N)
        longitude: Observer longitude (default: home location 78.73W)
    """
    observer = _get_observer(lat=latitude, lon=longitude)
    t = _parse_time(date)

    sunset = observer.sun_set_time(t, which="next")
    sunrise = observer.sun_rise_time(t + 1 * u.day, which="next")
    midnight = Time((sunset.jd + sunrise.jd) / 2, format="jd")

    constraints = [
        AltitudeConstraint(min=min_altitude * u.deg, max=85 * u.deg),
        MoonSeparationConstraint(min=min_moon_separation * u.deg),
    ]

    kwargs = {"uptovmag": max_magnitude}
    if object_type:
        kwargs["type"] = [object_type]

    try:
        dso_list = listObjects(**kwargs)
    except Exception as e:
        return [{"error": str(e)}]

    targets = []
    for obj in dso_list:
        ft = _dso_to_target(obj)
        if ft:
            targets.append((obj, ft))

    if not targets:
        return [{"message": "No catalog objects matched the filters"}]

    dso_objects, fixed_targets = zip(*targets)
    fixed_targets = list(fixed_targets)

    try:
        observable = is_observable(
            constraints, observer, fixed_targets,
            time_range=[sunset, sunrise],
        )
    except Exception as e:
        return [{"error": f"Observability check failed: {e}"}]

    results = []
    for obs_flag, obj, ft in zip(observable, dso_objects, fixed_targets):
        if not obs_flag:
            continue

        try:
            altaz = observer.altaz(midnight, ft)
            alt = altaz.alt.deg
            az = altaz.az.deg
        except Exception:
            alt, az = 0, 0

        mags = obj.magnitudes
        dims = obj.dimensions
        ids = obj.identifiers

        results.append({
            "name": obj.name,
            "type": obj.type,
            "constellation": obj.constellation,
            "magnitude": mags[1] if mags and mags[1] is not None else (mags[0] if mags else None),
            "major_axis_arcmin": dims[0] if dims else None,
            "midnight_altitude_deg": round(alt, 1),
            "midnight_azimuth_deg": round(az, 1),
            "common_names": ids[3] if ids and len(ids) > 3 else [],
        })

    results.sort(key=lambda x: -(x.get("midnight_altitude_deg") or 0))
    return results[:limit]


def get_altitude_profile(
    target_name: str,
    date: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get altitude vs time profile for a target throughout the night.

    Returns hourly altitude readings from sunset to sunrise, useful for
    planning when to image a target. Flags the optimal imaging window.

    Args:
        target_name: Object name (e.g. "M31", "NGC 7000")
        date: ISO 8601 date (default: tonight). Example: "2026-03-31"
        latitude: Observer latitude (default: home location 35.65N)
        longitude: Observer longitude (default: home location 78.73W)
    """
    observer = _get_observer(lat=latitude, lon=longitude)
    t = _parse_time(date)

    sunset = observer.sun_set_time(t, which="next")
    sunrise = observer.sun_rise_time(t + 1 * u.day, which="next")

    target = _resolve_target(target_name)
    if not target:
        return {"error": f"Could not find '{target_name}'"}

    hours = int((sunrise - sunset).sec / 3600)
    profile = []
    peak_alt = -90
    peak_time = None

    for h in range(hours + 1):
        check_time = sunset + h * u.hour
        try:
            altaz = observer.altaz(check_time, target)
            alt = round(altaz.alt.deg, 1)
            az = round(altaz.az.deg, 1)
            profile.append({
                "time_utc": check_time.iso,
                "altitude_deg": alt,
                "azimuth_deg": az,
            })
            if alt > peak_alt:
                peak_alt = alt
                peak_time = check_time.iso
        except Exception:
            continue

    good_window = [p for p in profile if p["altitude_deg"] >= 30]

    return {
        "target": target_name,
        "sunset_utc": sunset.iso,
        "sunrise_utc": sunrise.iso,
        "peak_altitude_deg": round(peak_alt, 1),
        "peak_time_utc": peak_time,
        "imaging_window_hours": len(good_window),
        "profile": profile,
    }
