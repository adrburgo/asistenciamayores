#!/usr/bin/env bash
# Configuración inicial del sistema. Ejecutar una vez antes del primer arranque.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Setup: Sistema de Asistencia para Mayores ==="

# 1. Crear .env si no existe
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[OK] Creado .env desde .env.example. Edítalo con tus valores antes de continuar."
else
  echo "[OK] .env ya existe."
fi

# 2. Leer solo las variables que necesita este script del .env
#    (no se hace source para evitar problemas con valores JSON o con espacios)
_env_get() {
  grep -E "^${1}=" .env | tail -1 | cut -d'=' -f2- | sed "s/^['\"]//;s/['\"]$//"
}
MQTT_USER="$(_env_get MQTT_USER)"
MQTT_PASSWORD="$(_env_get MQTT_PASSWORD)"
OLLAMA_MODEL_DEV="$(_env_get OLLAMA_MODEL_DEV)"
OLLAMA_MODEL_PROD="$(_env_get OLLAMA_MODEL_PROD)"
: "${MQTT_USER:=asistente}"
: "${OLLAMA_MODEL_DEV:=llama3.2:3b}"
: "${OLLAMA_MODEL_PROD:=llama3.2:3b}"

# 3. Crear contraseña MQTT
echo ""
echo "=== Configurando MQTT ==="
if [ ! -f config/mosquitto/passwd ]; then
  if command -v mosquitto_passwd &>/dev/null; then
    mosquitto_passwd -c -b config/mosquitto/passwd "$MQTT_USER" "$MQTT_PASSWORD"
  else
    echo "[!] mosquitto_passwd no encontrado. Creando passwd vía Docker..."
    docker run --rm -v "$ROOT_DIR/config/mosquitto:/mosquitto/config" \
      eclipse-mosquitto:2 \
      mosquitto_passwd -c -b /mosquitto/config/passwd "$MQTT_USER" "$MQTT_PASSWORD"
  fi
  # El fichero puede quedar como root si se creó vía Docker; mosquitto necesita leerlo
  chmod 644 config/mosquitto/passwd
  echo "[OK] Fichero de contraseñas MQTT creado."
else
  echo "[OK] Fichero passwd MQTT ya existe."
fi

# 4. Descargar modelos Ollama
echo ""
echo "=== Descargando modelos Ollama ==="
docker compose up -d ollama
sleep 5
OLLAMA_HOST=localhost OLLAMA_PORT=11434 \
OLLAMA_MODEL_DEV="${OLLAMA_MODEL_DEV:-llama3.2:3b}" \
OLLAMA_MODEL_PROD="${OLLAMA_MODEL_PROD:-llama3.2:3b}" \
  bash config/ollama/preload_models.sh
docker compose stop ollama

# 5. Verificar permisos de audio
echo ""
echo "=== Verificando audio ==="
if [ -d /dev/snd ]; then
  echo "[OK] Dispositivos de audio detectados."
else
  echo "[!] No se encontraron dispositivos /dev/snd. Comprueba el micrófono."
fi

echo ""
echo "=== Setup completado ==="
echo ""
echo "Próximos pasos:"
echo "  1. Edita .env con tus valores (teléfono de emergencias, contactos familiares)"
echo "  2. Configura las cámaras en config/frigate/frigate.yml"
echo "  3. Arranca en modo desarrollo:  ./scripts/start-dev.sh"
echo "  4. Arranca en modo producción:  ./scripts/start-prod.sh"
echo "  5. Accede a Home Assistant en:  http://$(hostname -I | awk '{print $1}'):8123"
echo "  6. Accede a Frigate en:         http://$(hostname -I | awk '{print $1}'):5000"
