from mcp.server.fastmcp import FastMCP

from astrobot_mcp.tools import astrospheric, dso, ephemeris, planning

mcp = FastMCP("astrobot-mcp", stateless_http=True)


# --- Astrospheric (weather/atmospheric) ---

@mcp.tool()
async def get_forecast(
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get 81-hour astrophotography weather forecast from Astrospheric.

    Returns cloud cover, seeing (0-5), transparency (0-5), temperature,
    dew point, and wind forecasts. Results are cached for 1 hour to conserve
    API credits (100/day). Defaults to home observatory location.
    """
    return await astrospheric.get_forecast(latitude, longitude)


@mcp.tool()
async def get_sky(
    latitude: float | None = None,
    longitude: float | None = None,
    timestamp_ms: int | None = None,
) -> dict:
    """Get current positions of bright stars, planets, Moon, and Sun from Astrospheric.

    Returns altitude/azimuth/RA/Dec for stars under mag 5, all planets,
    Moon (with phase and illumination), and Sun. Costs 1 API credit.
    """
    return await astrospheric.get_sky(latitude, longitude, timestamp_ms)


# --- DSO Catalog (PyOngc) ---

@mcp.tool()
def lookup_dso(name: str) -> dict:
    """Look up a deep sky object by name or catalog designation.

    Searches NGC/IC/Messier/Caldwell catalogs. Returns coordinates, magnitude,
    angular size, type, constellation, surface brightness, and common names.

    Examples: "M31", "NGC 7000", "IC 1396", "Andromeda Galaxy"
    """
    return dso.lookup_dso(name)


@mcp.tool()
def search_dsos(
    object_type: str | None = None,
    constellation: str | None = None,
    max_magnitude: float | None = None,
    min_size_arcmin: float | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search the deep sky object catalog with filters.

    Filter by object type, constellation, brightness, and angular size.
    Results sorted by brightness. Types: Galaxy, Nebula, Cluster,
    Open Cluster, Globular Cluster, Planetary Nebula, Supernova Remnant.
    Constellations use 3-letter codes (Ori, Cyg, Sgr, etc).
    """
    return dso.search_dsos(object_type, constellation, max_magnitude, min_size_arcmin, limit)


# --- Ephemeris (Skyfield) ---

@mcp.tool()
def get_planet_position(
    body: str,
    time: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get the position of a solar system body.

    Returns altitude, azimuth, RA, Dec, and distance for any planet,
    the Moon, or the Sun. Valid bodies: mercury, venus, mars, jupiter,
    saturn, uranus, neptune, moon, sun.
    """
    return ephemeris.get_planet_position(body, time, latitude, longitude)


@mcp.tool()
def get_moon_info(
    time: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get detailed Moon information.

    Returns phase name, illumination percentage, phase angle, position
    (altitude/azimuth/RA/Dec), and distance. Essential for planning
    deep sky imaging sessions (bright Moon washes out faint targets).
    """
    return ephemeris.get_moon_info(time, latitude, longitude)


# --- Observation Planning (astroplan) ---

@mcp.tool()
def get_rise_set_transit(
    target_name: str,
    date: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get rise, set, and transit times for a deep sky object or star.

    Returns when the target rises, transits the meridian (highest point),
    and sets. Also reports transit altitude and whether the object is
    circumpolar. Works with DSO names (M31, NGC 7000) and star names (Vega).
    """
    return planning.get_rise_set_transit(target_name, date, latitude, longitude)


@mcp.tool()
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
    """Find deep sky objects visible tonight that meet imaging constraints.

    Checks the full catalog against altitude, magnitude, and Moon separation
    constraints for the night. Returns objects sorted by midnight altitude
    (best-positioned first). Factor in southern horizon obstruction (~25 deg)
    when reviewing results with southern azimuths (150-210 deg).
    """
    return planning.whats_visible(
        date, min_altitude, max_magnitude, min_moon_separation,
        object_type, limit, latitude, longitude,
    )


@mcp.tool()
def get_altitude_profile(
    target_name: str,
    date: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get hourly altitude profile for a target throughout the night.

    Returns altitude readings from sunset to sunrise, peak altitude and time,
    and the number of hours above 30 degrees (imaging window). Use this to
    plan when to start and stop imaging a specific target.
    """
    return planning.get_altitude_profile(target_name, date, latitude, longitude)


def main():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
