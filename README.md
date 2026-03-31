# astrobot-mcp

MCP server for astrophotography planning — weather forecasts, DSO catalog, planetary ephemeris, and observation planning.

Built for use with [OpenClaw](https://openclaw.rocks) AstroBot agent but works with any MCP client.

## Tools

### Weather & Atmospheric (Astrospheric API)
- **get_forecast** — 81-hour cloud cover, seeing, transparency, temperature, dew point, wind
- **get_sky** — Positions of bright stars, planets, Moon (with phase), and Sun

### Deep Sky Object Catalog (PyOngc)
- **lookup_dso** — Look up any NGC/IC/Messier/Caldwell object by name
- **search_dsos** — Filter catalog by type, constellation, magnitude, size

### Planetary Ephemeris (Skyfield)
- **get_planet_position** — Altitude, azimuth, RA/Dec for any planet, Moon, or Sun
- **get_moon_info** — Phase, illumination, position, distance

### Observation Planning (astroplan)
- **get_rise_set_transit** — Rise, set, and transit times for any target
- **whats_visible** — Find DSOs visible tonight with altitude and Moon constraints
- **get_altitude_profile** — Hourly altitude profile for imaging window planning

## Running Locally

```bash
pip install -e .
ASTROSPHERIC_API_KEY=your-key SKYFIELD_DATA_DIR=./skyfield-data astrobot-mcp
```

## Running Tests

```bash
pip install -e ".[test]"
pytest tests/ -v
```

## Docker

```bash
docker build -t astrobot-mcp .
docker run -p 8080:8080 -e ASTROSPHERIC_API_KEY=your-key astrobot-mcp
```

## Kubernetes

```bash
kubectl create secret generic astrobot-mcp-secrets \
  --namespace astrobot-mcp \
  --from-literal=ASTROSPHERIC_API_KEY='your-key'

kubectl apply -f k8s/deployment.yml
```

## Architecture

- **Transport**: Streamable HTTP on port 8080
- **DSO data**: Local SQLite database via PyOngc (13,226 NGC/IC objects, zero API calls)
- **Ephemeris**: JPL DE421 via Skyfield (baked into Docker image)
- **Planning**: astroplan for visibility, constraints, rise/set/transit (local computation)
- **Weather**: Astrospheric API (100 credits/day, cached to conserve credits)
