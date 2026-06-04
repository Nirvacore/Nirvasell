# nirva.sell — production image
#
# Multi-stage build: builder compiles wheels with build-essential; runtime is
# a slim image with no compilers (smaller attack surface). Runs as non-root.
#
# Build:  docker build -t nirva-sell .
# Run:    docker run -p 8501:8501 -v $(pwd)/data:/app/data --env-file .env nirva-sell

# ---------- builder ----------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Compile-time deps (rembg's onnxruntime, Pillow image-format support)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# ---------- runtime ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Runtime libs only — no compilers in the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libjpeg62-turbo \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user — better security posture
RUN groupadd -r nirva && useradd -r -g nirva -d /app -s /sbin/nologin nirva

WORKDIR /app

# Install pre-built wheels from the builder stage
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

# App code last so requirement changes don't bust this layer
COPY --chown=nirva:nirva . .

# Persistent data dir (user DBs, scraped images, generated content)
RUN mkdir -p /app/data /app/data/users && chown -R nirva:nirva /app/data

USER nirva

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
