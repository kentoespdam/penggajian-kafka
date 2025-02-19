FROM python:3.12.7-alpine3.20 AS base
RUN apk add --no-cache tk
WORKDIR /project
RUN mkdir logs
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
FROM base AS production
COPY . .
CMD ["fastapi","run", "main.py", "--port", "80"]
