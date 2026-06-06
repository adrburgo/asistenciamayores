FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    ffmpeg \
    alsa-utils \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar piper TTS como binario (multi-arquitectura)
RUN ARCH=$(uname -m) && \
    PIPER_ARCH=$([ "$ARCH" = "aarch64" ] && echo "aarch64" || echo "x86_64") && \
    curl -fsSL "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_${PIPER_ARCH}.tar.gz" \
    | tar -xzC /usr/local/lib && \
    ln -sf /usr/local/lib/piper/piper /usr/local/bin/piper

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Desarrollo ──────────────────────────────────────────────────────────────
FROM base AS development
RUN pip install --no-cache-dir watchdog
COPY src/ ./src/
CMD ["python", "-m", "watchdog.watchmedo", "auto-restart", "--directory=./src", "--pattern=*.py", "--", "python", "-m", "src.main"]

# ── Producción ──────────────────────────────────────────────────────────────
FROM base AS production
COPY src/ ./src/
CMD ["python", "-m", "src.main"]
