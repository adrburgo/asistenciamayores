#!/usr/bin/env bash
# Instala el servicio systemd para que el sistema arranque automáticamente con el miniordenador.
# Ejecutar con: sudo ./scripts/install-service.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="/opt/asistenciamayores"
SERVICE_NAME="asistenciamayores"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: Este script debe ejecutarse como root (sudo)."
  exit 1
fi

echo "=== Instalando servicio systemd: $SERVICE_NAME ==="

# 1. Copiar el proyecto a /opt si no está ya allí
if [ "$ROOT_DIR" != "$INSTALL_DIR" ]; then
  echo "Copiando proyecto a $INSTALL_DIR..."
  mkdir -p "$INSTALL_DIR"
  rsync -av --exclude='env/' --exclude='*.pyc' --exclude='.git/' "$ROOT_DIR/" "$INSTALL_DIR/"
  echo "[OK] Proyecto copiado."
else
  echo "[OK] El proyecto ya está en $INSTALL_DIR."
fi

# 2. Instalar el fichero de servicio
cp "$INSTALL_DIR/systemd/$SERVICE_NAME.service" "/etc/systemd/system/$SERVICE_NAME.service"
echo "[OK] Fichero de servicio instalado en /etc/systemd/system/"

# 3. Recargar systemd y habilitar el servicio
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
echo "[OK] Servicio habilitado. Se iniciará automáticamente al arrancar."

# 4. Iniciar ahora
echo ""
read -r -p "¿Iniciar el sistema ahora? [s/N] " answer
if [[ "$answer" =~ ^[sS]$ ]]; then
  systemctl start "$SERVICE_NAME"
  echo "[OK] Sistema iniciado."
  echo ""
  echo "Estado:"
  systemctl status "$SERVICE_NAME" --no-pager
fi

echo ""
echo "=== Instalación completada ==="
echo ""
echo "Comandos útiles:"
echo "  sudo systemctl status  $SERVICE_NAME   # Ver estado"
echo "  sudo systemctl restart $SERVICE_NAME   # Reiniciar"
echo "  sudo systemctl stop    $SERVICE_NAME   # Parar"
echo "  sudo journalctl -u     $SERVICE_NAME -f # Ver logs"
