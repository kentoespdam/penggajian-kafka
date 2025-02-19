FROM python:3.12.7-alpine3.20 AS base
RUN apk add --no-cache tk
WORKDIR /app
COPY . .
RUN mkdir logs
RUN pip install --no-cache-dir --find-links=/app/wheelhouse --only-binary=:all: -r requirements.txt
CMD ["fastapi","run", "main.py", "--port", "80"]
