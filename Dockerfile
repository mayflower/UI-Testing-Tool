# Stage 1: Python dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Production image with Playwright browsers
FROM python:3.12-slim

# System-Abhängigkeiten fuer Playwright Chromium + Non-root User
# (verhindert Root-Laufzeit im Container)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libwayland-client0 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash --uid 1001 appuser

WORKDIR /app

# Python-Pakete aus Builder-Stage
COPY --from=builder /install /usr/local

# Anwendung kopieren — root-owned, fuer appuser read-only
COPY app.py run.py conftest.py pyproject.toml ./
COPY config/ ./config/
COPY utils/ ./utils/
COPY tests/ ./tests/
COPY templates/ ./templates/
COPY static/ ./static/

# Nur echte Laufzeit-Verzeichnisse beschreibbar machen:
# config/ wird von der Settings-UI beschrieben (environments/selectors/jira.yaml)
RUN mkdir -p reports screenshots /home/appuser/.cache \
    && chown -R appuser:appuser config reports screenshots /home/appuser/.cache

USER appuser

# Playwright Chromium als appuser installieren (Cache in ~/.cache/ms-playwright)
RUN playwright install chromium

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0

EXPOSE 5000

CMD ["python", "app.py"]
