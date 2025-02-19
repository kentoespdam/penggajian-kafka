# FROM python:3.14.0a5-slim-bookworm AS base

FROM python:3.9-slim-buster AS builder
WORKDIR /app
# RUN apt update && apt install pkg-config build-essential gcc make rustc cargo -y
RUN pip install "fastapi[standard]" openpyxl apscheduler python-dotenv icecream pymysql-pool aiokafka swifter asyncio
# COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS production
WORKDIR /app
COPY --from=builder /app/lib/python3.9 /app/lib/python3.9
COPY . .
CMD ["fastapi","run", "app/main.py", "--port", "80"]