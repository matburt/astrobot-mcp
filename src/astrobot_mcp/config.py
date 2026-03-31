import os

ASTROSPHERIC_API_KEY = os.environ.get("ASTROSPHERIC_API_KEY", "")
ASTROSPHERIC_BASE_URL = "https://astrosphericpublicaccess.azurewebsites.net/api"

DEFAULT_LAT = 35.6481
DEFAULT_LON = -78.7274
DEFAULT_ELEVATION = 100.0  # meters, approximate for Raleigh area

# Skyfield ephemeris file (cached on persistent volume)
SKYFIELD_DATA_DIR = os.environ.get("SKYFIELD_DATA_DIR", "/data/skyfield")

# Astrospheric forecast cache TTL (seconds) — forecasts update every 6 hours
FORECAST_CACHE_TTL = 3600  # 1 hour is plenty given 6hr update cycle

# Minimum altitude for southern objects (tree obstruction)
SOUTH_HORIZON_MIN_ALT = 25.0
