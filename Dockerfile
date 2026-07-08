# ============================================================
# Discord Management Platform — Bot Dockerfile
# ============================================================
# Multi-stage build for minimal production image size.
# Stage 1: Install dependencies into a virtual environment.
# Stage 2: Copy only the venv and application code.
# ============================================================

FROM python:3.10-slim AS builder

WORKDIR /build

# Install system dependencies required by WeasyPrint and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libpq-dev \
    libjpeg62-turbo-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------
# Stage 2: Production image
# ----------------------------------------------------------
FROM python:3.10-slim AS production

WORKDIR /app

# Runtime system dependencies for Pillow / WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application code
COPY bot/ ./bot/
COPY dashboard/ ./dashboard/
COPY locales/ ./locales/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY pyproject.toml .

# Create non-root user
RUN groupadd -r botuser && useradd -r -g botuser botuser \
    && mkdir -p /app/data/transcripts \
    && chown -R botuser:botuser /app
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-m", "bot"]
