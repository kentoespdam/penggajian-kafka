FROM python:3.12.9-slim-bookworm AS base
WORKDIR /app

FROM base AS builder
WORKDIR /app
COPY wheelhouse ./wheelhouse
COPY requirements.txt .
RUN pip install --no-cache-dir --find-links=wheelhouse --only-binary=:all: -r requirements.txt

FROM base AS runner
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY core ./core
COPY excel_template ./excel_template
COPY main.py ./main.py
RUN mkdir logs result_excel
RUN touch logs/penggajian.log
RUN rm -rf wheelhouse
CMD ["fastapi","run", "main.py", "--port", "80"]