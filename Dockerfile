FROM python:3.14.0a5-slim-bookworm AS base
WORKDIR /app
RUN python -m venv .venv
RUN source .venv/bin/activate
RUN pip install "fastapi[standard]" "dask[dataframe]" openpyxl apscheduler python-dotenv icecream pymysql-pool aiokafka 
FROM base AS production
WORKDIR /app
COPY . .
RUN source .venv/bin/activate
CMD ["fastapi","run", "app/main.py", "--port", "80"]