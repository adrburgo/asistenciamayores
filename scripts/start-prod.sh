#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Iniciando en modo PRODUCCIÓN ==="
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up --build -d "$@"

echo ""
echo "Servicios iniciados en background. Comprueba el estado con:"
echo "  docker compose ps"
echo "  docker compose logs -f"
