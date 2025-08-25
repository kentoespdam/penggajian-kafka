# Base image aligned with project Python version
FROM python:3.12.10-alpine3.21 AS base

# Extracted constants
ARG APP_HOME=/app
ARG UID=1001
ARG GID=1001

WORKDIR ${APP_HOME}

# System packages needed at runtime and for building in derived stages
RUN apk add --no-cache \
    git openssl libstdc++ librdkafka bash curl linux-headers gcc musl-dev libffi-dev

# Builder stage: compile/install dependencies into a venv
FROM base AS builder
ENV PIP_NO_CACHE_DIR=1
WORKDIR ${APP_HOME}
RUN apk add --no-cache \
    g++ libc-dev make cmake openssl-dev zlib-dev librdkafka-dev
RUN python3 -m venv .venv
ENV PATH=${APP_HOME}/.venv/bin:$PATH
COPY requirements-old.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Final runtime image
FROM base AS final
WORKDIR ${APP_HOME}

# Create non-root user/group once with extracted IDs
RUN addgroup -S -g ${GID} prod && \
    adduser  -S -u ${UID} -G prod -h ${APP_HOME} prod

# Copy venv and application files with correct ownership
COPY --from=builder --chown=prod:prod ${APP_HOME}/.venv ${APP_HOME}/.venv
COPY --chown=prod:prod core excel_template main.py .env ${APP_HOME}/

# Switch to non-root user before creating writable directories
USER prod
RUN mkdir -p ${APP_HOME}/result_excel

# Ensure venv is first on PATH
ENV PATH=${APP_HOME}/.venv/bin:$PATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]