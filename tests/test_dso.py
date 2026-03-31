from astrobot_mcp.tools.dso import lookup_dso, search_dsos


class TestLookupDso:
    def test_messier_object(self):
        result = lookup_dso("M31")
        assert result["name"] == "NGC0224"
        assert result["type"] == "Galaxy"
        assert result["constellation"] == "And"
        assert result["magnitude"] is not None
        assert result["major_axis_arcmin"] is not None
        assert "Andromeda Galaxy" in result["common_names"]

    def test_ngc_object(self):
        result = lookup_dso("NGC 7000")
        assert result["name"] == "NGC7000"
        assert "North America Nebula" in result["common_names"]

    def test_ic_object(self):
        result = lookup_dso("IC 1396")
        assert result["name"] == "IC1396"

    def test_not_found(self):
        result = lookup_dso("FAKE12345")
        assert "error" in result

    def test_has_coordinates(self):
        result = lookup_dso("M42")
        assert result["ra"] is not None
        assert result["dec"] is not None

    def test_has_hubble_type_for_galaxy(self):
        result = lookup_dso("M31")
        assert result["hubble_type"] is not None


class TestSearchDsos:
    def test_search_by_type(self):
        results = search_dsos(object_type="PN", max_magnitude=12, limit=10)
        assert len(results) > 0
        assert all("Nebula" in r["type"] for r in results if "error" not in r)

    def test_search_by_constellation(self):
        results = search_dsos(constellation="Ori", limit=10)
        assert len(results) > 0
        assert all(r["constellation"] == "Ori" for r in results if "error" not in r)

    def test_search_by_magnitude(self):
        results = search_dsos(max_magnitude=6, limit=10)
        assert len(results) > 0
        for r in results:
            if r.get("magnitude"):
                assert r["magnitude"] <= 6

    def test_search_sorted_by_brightness(self):
        results = search_dsos(max_magnitude=10, limit=10)
        mags = [r["magnitude"] for r in results if r.get("magnitude") is not None]
        assert mags == sorted(mags)

    def test_search_with_min_size(self):
        results = search_dsos(min_size_arcmin=30, max_magnitude=10, limit=10)
        assert len(results) > 0
        for r in results:
            if r.get("major_axis_arcmin"):
                assert r["major_axis_arcmin"] >= 30

    def test_search_messier_catalog(self):
        results = search_dsos(catalog="M", limit=200)
        assert len(results) > 100  # there are 110 Messier objects

    def test_limit_respected(self):
        results = search_dsos(max_magnitude=15, limit=5)
        assert len(results) <= 5

    def test_common_names_filter(self):
        results = search_dsos(with_common_name=True, max_magnitude=8, limit=10)
        assert len(results) > 0
        for r in results:
            assert len(r.get("common_names", [])) > 0
