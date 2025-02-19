FROM python:3.14.0a5 AS base
WORKDIR /app

FROM base AS builder
WORKDIR /app
RUN apt update && apt install pkg-config build-essential -y
RUN python -m venv .venv
ENV PATH=".venv/bin:$PATH"
RUN pip install "fastapi[standard]" openpyxl apscheduler python-dotenv icecream pymysql-pool aiokafka swifter
# COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS production
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH=".venv/bin:$PATH"
CMD ["fastapi","run", "app/main.py", "--port", "80"]