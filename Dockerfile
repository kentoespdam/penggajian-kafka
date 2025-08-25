FROM python:3.12.9-alpine3.21 AS base
WORKDIR /app
RUN apk add --no-cache git openssl libstdc++ librdkafka bash curl linux-headers gcc musl-dev libffi-dev

FROM base AS builder
WORKDIR /app
RUN apk update && apk add --no-cache \
    g++ \
    libc-dev \
    make \
    cmake \
    openssl-dev \
    zlib-dev

RUN apk add --no-cache librdkafka-dev
RUN python3 -m venv .venv
ENV PATH /app/.venv/bin:$PATH
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install -r requirements.txt

FROM base AS runner
USER 1001:1001
WORKDIR /app
# RUN git clone https://github.com/kentoespdam/penggajian-kafka.git -b v1.0.0 .
COPY --from=builder --chown=1001:1001 /app/.venv /app/.venv
COPY core ./core
COPY excel_template ./excel_template
COPY main.py ./main.py
COPY .env .
RUN mkdir -p /app/result_excel
ENV PATH /app/.venv/bin:$PATH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]