# --------------------------------------------------------------------------- #
# FTO Program — production Docker image
# Multi-stage build: builder installs wheels, runtime is slim + non-root.
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Build deps for psycopg2 (only needed at build time)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir=/wheels -r requirements.txt


# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production \
    SQLITE_PATH=/var/lib/fto/fto.db \
    PORT=8000

# Runtime libs only — no compilers
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl tini \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --system --gid 10001 fto \
    && useradd --system --uid 10001 --gid fto --home /app --shell /usr/sbin/nologin fto

WORKDIR /app

# Install wheels built in stage 1
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Application code
COPY --chown=fto:fto . .

# Persistent data dir for SQLite (mount a volume here)
RUN mkdir -p /var/lib/fto && chown fto:fto /var/lib/fto

USER fto

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:${PORT}/healthz || exit 1

# tini reaps zombies; entrypoint bootstraps admin then starts gunicorn
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "python seed.py --bootstrap && exec gunicorn --config gunicorn.conf.py wsgi:app"]
