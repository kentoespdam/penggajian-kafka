FROM python:3.12.9-slim-bookworm AS base
WORKDIR /app
COPY wheelhouse ./wheelhouse
COPY requirements.txt .
RUN pip install --no-cache-dir --find-links=wheelhouse --only-binary=:all: -r requirements.txt
FROM base AS runner
WORKDIR /app
COPY . .
RUN mkdir logs result_excel
RUN rm -rf wheelhouse
CMD ["fastapi","run", "main.py", "--port", "80", "&&","tail","-f","logs/penggajian.log"]