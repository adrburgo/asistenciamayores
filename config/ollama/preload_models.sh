#!/usr/bin/env bash
# Descarga los modelos Ollama necesarios al iniciar el sistema.
# Ejecutado por scripts/setup.sh

set -e

OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
BASE_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"

pull_model() {
  local model="$1"
  echo "Descargando modelo: $model"
  curl -s -X POST "${BASE_URL}/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"${model}\"}" | grep -v "^$"
  echo "Modelo $model listo."
}

echo "Esperando a que Ollama esté disponible..."
until curl -sf "${BASE_URL}/api/tags" > /dev/null; do
  sleep 2
done

pull_model "${OLLAMA_MODEL_DEV:-llama3.2:3b}"

if [ "${PULL_PROD_MODEL:-false}" = "true" ]; then
  pull_model "${OLLAMA_MODEL_PROD:-llama3.2:3b}"
fi

echo "Modelos Ollama listos."
