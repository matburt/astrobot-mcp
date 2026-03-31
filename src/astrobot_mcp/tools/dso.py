from pyongc.ongc import Dso, get as ongc_get, listObjects


def lookup_dso(name: str) -> dict:
    """Look up a deep sky object by name or catalog designation.

    Searches the NGC/IC/Messier/Caldwell catalogs. Returns coordinates,
    magnitude, angular size, object type, constellation, and common names.

    Args:
        name: Object name (e.g. "M31", "NGC 7000", "IC 1396")
    """
    obj = ongc_get(name)
    if obj is not None:
        return _format_object(obj)

    try:
        results = listObjects(cname=name)
        if results:
            return _format_object(results[0])
    except Exception:
        pass

    return {"error": f"Object '{name}' not found in NGC/IC catalogs"}


def search_dsos(
    object_type: str | None = None,
    constellation: str | None = None,
    max_magnitude: float | None = None,
    min_size_arcmin: float | None = None,
    max_size_arcmin: float | None = None,
    catalog: str | None = None,
    with_common_name: bool = False,
    limit: int = 20,
) -> list[dict]:
    """Search the DSO catalog with filters.

    Returns a list of deep sky objects matching the criteria, sorted by
    brightness (lowest magnitude first).

    Args:
        object_type: Filter by type code — "*", "**", "OC", "GC", "Cl+N", "G", "GPair", "GTrpl", "GGroup", "PN", "HII", "DrkN", "EmN", "Neb", "RfN", "SNR", "Nova", "NonEx", "Dup", "Other"
        constellation: Three-letter constellation abbreviation (e.g. "Ori", "Cyg", "Sgr")
        max_magnitude: Maximum visual magnitude (e.g. 10.0 for objects brighter than mag 10)
        min_size_arcmin: Minimum major axis size in arcminutes
        max_size_arcmin: Maximum major axis size in arcminutes
        catalog: Filter by catalog — "NGC", "IC", or "M"
        with_common_name: Only return objects that have a common name
        limit: Maximum results to return (default 20)
    """
    kwargs = {}
    if object_type:
        kwargs["type"] = [object_type]
    if constellation:
        kwargs["constellation"] = [constellation]
    if max_magnitude is not None:
        kwargs["uptovmag"] = max_magnitude
    if min_size_arcmin is not None:
        kwargs["minsize"] = min_size_arcmin
    if max_size_arcmin is not None:
        kwargs["maxsize"] = max_size_arcmin
    if catalog:
        kwargs["catalog"] = catalog
    if with_common_name:
        kwargs["withname"] = True

    try:
        results = listObjects(**kwargs)
    except Exception as e:
        return [{"error": str(e)}]

    formatted = [_format_object(obj) for obj in results]
    formatted = [o for o in formatted if "error" not in o]
    formatted.sort(key=lambda x: x.get("magnitude") or 99)
    return formatted[:limit]


def _format_object(obj: Dso) -> dict:
    try:
        mags = obj.magnitudes  # (B, V, J, H, K) tuple
        dims = obj.dimensions  # (major, minor, pa) tuple
        ids = obj.identifiers  # (messier, ngc/ic, other_catalogs, common_names, other_ids)

        common_names = ids[3] if ids and len(ids) > 3 else []
        messier = ids[0] if ids else None

        return {
            "name": obj.name,
            "type": obj.type,
            "constellation": obj.constellation,
            "ra": obj.ra,
            "dec": obj.dec,
            "magnitude": mags[1] if mags and mags[1] is not None else (mags[0] if mags else None),
            "surface_brightness": obj.surface_brightness,
            "major_axis_arcmin": dims[0] if dims else None,
            "minor_axis_arcmin": dims[1] if dims else None,
            "position_angle": dims[2] if dims else None,
            "common_names": common_names,
            "messier": messier,
            "hubble_type": obj.hubble,
        }
    except Exception as e:
        return {"name": str(obj), "error": str(e)}
