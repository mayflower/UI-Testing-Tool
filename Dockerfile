# Stage 1: Python dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Production image with Playwright browsers
FROM python:3.12-slim

WORKDIR /app

# System-Abhängigkeiten fuer Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*

# Python-Pakete aus Builder-Stage
COPY --from=builder /install /usr/local

# Anwendung kopieren
COPY app.py run.py conftest.py pyproject.toml ./
COPY config/ ./config/
COPY utils/ ./utils/
COPY tests/ ./tests/
COPY templates/ ./templates/
COPY static/ ./static/

# Verzeichnisse fuer Reports und Screenshots (werden zur Laufzeit gefuellt)
RUN mkdir -p reports screenshots

# Playwright Chromium installieren
RUN playwright install chromium

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "app.py"]
