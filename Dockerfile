# FROM python:3.14.0a5-slim-bookworm AS base
FROM ubuntu/python:3.12-24.04_stable AS base
WORKDIR /app

FROM base AS builder
WORKDIR /app
# RUN apt update && apt install pkg-config build-essential gcc make rustc cargo -y
RUN python3 -m venv .venv
ENV PATH=".venv/bin:$PATH"
RUN pip install "fastapi[standard]" openpyxl apscheduler python-dotenv icecream pymysql-pool aiokafka swifter asyncio
# COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS production
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH=".venv/bin:$PATH"
CMD ["fastapi","run", "app/main.py", "--port", "80"]