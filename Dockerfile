# Base image aligned with project Python version
FROM python:3.12.10-alpine3.21 AS base
# Extracted constants
ARG APP_HOME=/app
WORKDIR ${APP_HOME}
# System packages needed at runtime and for building in derived stages
RUN apk update && apk add --no-cache \
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
    linux-headers



# Builder stage: compile/install dependencies into a venv
FROM base AS builder
# Extracted constants
ARG APP_HOME=/app
WORKDIR ${APP_HOME}
RUN apk add --no-cache g++ libc-dev make cmake openssl-dev zlib-dev librdkafka-dev
RUN python3 -m venv .venv
ENV PATH=${APP_HOME}/.venv/bin:$PATH
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt




# Final runtime image
FROM base AS final
WORKDIR ${APP_HOME}
# Create non-root user
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app
# Copy venv and application files with correct ownership
COPY --from=builder --chown=appuser:appuser ${APP_HOME}/.venv ${APP_HOME}/.venv
COPY --chown=appuser:appuser . .
RUN chown -R appuser:appuser ${APP_HOME}
# Switch to non-root user before creating writable directories
USER appuser
RUN mkdir ${APP_HOME}/result_excel
# Ensure venv is first on PATH
ENV PATH=${APP_HOME}/.venv/bin:$PATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]