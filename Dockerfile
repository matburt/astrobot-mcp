FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY src/ src/

RUN uv pip install --system .

# Pre-download Skyfield ephemeris so it's baked into the image
RUN python -c "from skyfield.api import load; load.directory = '/data/skyfield'; import os; os.makedirs('/data/skyfield', exist_ok=True); load('de421.bsp')"

EXPOSE 8080

CMD ["astrobot-mcp"]
