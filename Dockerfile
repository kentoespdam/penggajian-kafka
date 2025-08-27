# Stage 1: Builder stage
FROM python:3.12.10-alpine3.21 AS builder
ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    make \
    build-base \
    openblas-dev \
    lapack-dev \
    gfortran \
    linux-headers \
    librdkafka-dev

RUN python3 -m venv .venv
ENV PATH=${APP_HOME}/.venv/bin:$PATH

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.12.10-alpine3.21
ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# Install runtime dependencies only
RUN apk add --no-cache \
    libstdc++ \
    openblas \
    librdkafka \
    curl

# Create non-root user
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser ${APP_HOME}

# Copy venv and application files with correct ownership
COPY --from=builder --chown=appuser:appuser ${APP_HOME}/.venv ${APP_HOME}/.venv
COPY --chown=appuser:appuser . .

USER appuser
RUN mkdir -p ${APP_HOME}/result_excel

ENV PATH=${APP_HOME}/.venv/bin:$PATH

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4"]