FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS development
RUN pip install --no-cache-dir watchdog
COPY src/ ./src/
CMD ["python", "-m", "watchdog.watchmedo", "auto-restart", "--directory=./src", "--pattern=*.py", "--", "python", "-m", "src.main"]

FROM base AS production
COPY src/ ./src/
CMD ["python", "-m", "src.main"]
