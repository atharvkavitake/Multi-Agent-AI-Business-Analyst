# Multi-stage production Dockerfile
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --user -r backend/requirements.txt

# Final lean runtime image
FROM python:3.10-slim AS runner

WORKDIR /app

# Install runtime PostgreSQL client library and fonts for ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Copy application source code
COPY backend ./backend
COPY frontend ./frontend
COPY data ./data

# Create directory structure for uploads, reports, and database
RUN mkdir -p /app/data/uploads /app/data/reports

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
