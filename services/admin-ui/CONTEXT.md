# admin-ui

## Propósito

Panel de administración web del sistema. Permite gestionar las cámaras de Frigate desde una interfaz gráfica (sin editar YAML) y monitorizar el estado de todos los servicios en tiempo real.

## Características

- **Dashboard**: estado de los 4 servicios Python (voice, ai, actions, vision) actualizado cada 10s via MQTT, última alerta de caída
- **Gestión de cámaras**: añadir cámaras IP (RTSP) o USB, eliminar, ver resolución y FPS — los cambios se aplican a `frigate.yml` y se recarga Frigate automáticamente
- **Accesos rápidos**: links a Home Assistant y Frigate UI

## Puerto

Accesible en `http://<ip>:8080`

## Tópicos MQTT (solo escucha, no publica)

| Tópico | Motivo |
|--------|--------|
| `asistente/estado` | Estado de voice/ai/action services |
| `caidas/estado` | Estado de vision-service |
| `caidas/alerta` | Última alerta de caída para mostrar en el dashboard |

## Volúmenes

Necesita acceso de **lectura/escritura** a `config/frigate/frigate.yml` para poder añadir/eliminar cámaras. Por eso el mount de Frigate se cambió a `rw` (sin `:ro`).

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `FRIGATE_HOST` / `FRIGATE_PORT` | Para llamar a la API de recarga de Frigate |
| `HA_URL` | Enlace al panel de HA |
| `MQTT_*` | Conexión al broker para leer estados |

## Ejecutar fuera de Docker

```bash
cd services/admin-ui
pip install -r requirements.txt
FRIGATE_HOST=localhost MQTT_HOST=localhost uvicorn src.main:app --reload --port 8080
```
