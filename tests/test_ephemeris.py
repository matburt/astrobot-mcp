import os
os.environ.setdefault("SKYFIELD_DATA_DIR", "/tmp/skyfield")

from astrobot_mcp.tools.ephemeris import get_planet_position, get_moon_info


class TestGetPlanetPosition:
    def test_jupiter(self):
        result = get_planet_position("jupiter")
        assert "altitude_deg" in result
        assert "azimuth_deg" in result
        assert "ra" in result
        assert "dec" in result
        assert "distance_au" in result
        assert result["body"] == "jupiter"

    def test_all_planets(self):
        for body in ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]:
            result = get_planet_position(body)
            assert "error" not in result, f"{body} failed: {result}"
            assert isinstance(result["altitude_deg"], float)

    def test_moon(self):
        result = get_planet_position("moon")
        assert "error" not in result
        assert result["distance_au"] < 0.01  # Moon is ~0.0026 AU

    def test_sun(self):
        result = get_planet_position("sun")
        assert "error" not in result
        assert 0.98 < result["distance_au"] < 1.02

    def test_invalid_body(self):
        result = get_planet_position("pluto")
        assert "error" in result

    def test_specific_time(self):
        result = get_planet_position("mars", time="2026-06-15T00:00:00")
        assert "error" not in result
        assert result["time_utc"] is not None

    def test_is_above_horizon_bool(self):
        result = get_planet_position("jupiter")
        assert isinstance(result["is_above_horizon"], bool)


class TestGetMoonInfo:
    def test_basic_info(self):
        result = get_moon_info()
        assert "phase_name" in result
        assert "illumination_pct" in result
        assert "phase_angle_deg" in result
        assert "altitude_deg" in result
        assert "distance_km" in result

    def test_illumination_range(self):
        result = get_moon_info()
        assert 0 <= result["illumination_pct"] <= 100

    def test_phase_name_valid(self):
        valid_phases = [
            "New Moon", "Waxing Crescent", "First Quarter",
            "Waxing Gibbous", "Full Moon", "Waning Gibbous",
            "Last Quarter", "Waning Crescent",
        ]
        result = get_moon_info()
        assert result["phase_name"] in valid_phases

    def test_specific_time(self):
        result = get_moon_info(time="2026-01-01T00:00:00")
        assert "error" not in result
