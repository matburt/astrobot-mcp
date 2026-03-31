import os
os.environ.setdefault("SKYFIELD_DATA_DIR", "/tmp/skyfield")

import pytest
from astrobot_mcp.tools.planning import get_rise_set_transit, whats_visible, get_altitude_profile


class TestGetRiseSetTransit:
    def test_m31(self):
        result = get_rise_set_transit("M31", date="2026-06-15T12:00:00")
        assert "error" not in result
        assert result["target"] == "M31"
        assert "rise_utc" in result
        assert "transit_utc" in result
        assert "set_utc" in result
        assert "transit_altitude_deg" in result

    def test_named_star(self):
        result = get_rise_set_transit("Vega", date="2026-06-15T12:00:00")
        assert "error" not in result
        assert result["transit_altitude_deg"] > 0

    def test_not_found(self):
        result = get_rise_set_transit("FAKEXYZ999")
        assert "error" in result

    def test_transit_altitude_reasonable(self):
        result = get_rise_set_transit("M42", date="2026-01-15T12:00:00")
        if "error" not in result:
            assert -90 <= result["transit_altitude_deg"] <= 90


class TestWhatsVisible:
    def test_returns_results(self):
        results = whats_visible(
            date="2026-06-15T12:00:00",
            max_magnitude=8,
            limit=10,
        )
        assert len(results) > 0
        assert "error" not in results[0]

    def test_has_expected_fields(self):
        results = whats_visible(
            date="2026-06-15T12:00:00",
            max_magnitude=6,
            limit=5,
        )
        if results and "error" not in results[0]:
            r = results[0]
            assert "name" in r
            assert "type" in r
            assert "constellation" in r
            assert "midnight_altitude_deg" in r

    def test_sorted_by_altitude(self):
        results = whats_visible(
            date="2026-06-15T12:00:00",
            max_magnitude=8,
            limit=10,
        )
        alts = [r["midnight_altitude_deg"] for r in results if "midnight_altitude_deg" in r]
        assert alts == sorted(alts, reverse=True)

    def test_limit_respected(self):
        results = whats_visible(
            date="2026-06-15T12:00:00",
            max_magnitude=10,
            limit=5,
        )
        assert len(results) <= 5

    def test_type_filter(self):
        results = whats_visible(
            date="2026-06-15T12:00:00",
            max_magnitude=10,
            object_type="PN",
            limit=10,
        )
        for r in results:
            if "type" in r:
                assert "Nebula" in r["type"]


class TestGetAltitudeProfile:
    def test_m42(self):
        result = get_altitude_profile("M42", date="2026-01-15T12:00:00")
        assert "error" not in result
        assert result["target"] == "M42"
        assert "profile" in result
        assert len(result["profile"]) > 0
        assert "peak_altitude_deg" in result
        assert "imaging_window_hours" in result

    def test_profile_has_hourly_data(self):
        result = get_altitude_profile("M31", date="2026-09-15T12:00:00")
        if "error" not in result:
            assert len(result["profile"]) >= 8  # at least 8 hours of night

    def test_sunset_sunrise_present(self):
        result = get_altitude_profile("M42", date="2026-01-15T12:00:00")
        assert "sunset_utc" in result
        assert "sunrise_utc" in result

    def test_not_found(self):
        result = get_altitude_profile("FAKEXYZ999")
        assert "error" in result
