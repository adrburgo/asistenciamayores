# action-controller

## Propósito

Recibe intents clasificados en `asistente/intent` y ejecuta la acción correspondiente. Cada intent tiene su propio handler en `src/actions/`. Las acciones interactúan con Home Assistant (via REST API) y con sistemas externos (llamadas telefónicas, etc.).

En modo desarrollo (`MOCK_ACTIONS=true`) todas las acciones se simulan y loguean sin ejecutar llamadas reales.

## Flujo

```
MQTT: asistente/intent → dispatcher → action handler → HA API / sistema
                                                      → MQTT: asistente/respuesta
```

## Tópicos MQTT

| Tópico | Tipo | Contenido |
|--------|------|-----------|
| `asistente/intent` | Suscribe | `{"intent": "...", "params": {...}, "confidence": 0.9}` |
| `asistente/respuesta` | Publica | `{"text": "..."}` — texto para que voice-service lo lea en voz alta |
| `asistente/estado` | Publica | `{"status": "online/offline/executing"}` |

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MOCK_ACTIONS` | `false` | Si `true`, no ejecuta acciones reales |
| `HA_URL` | `http://homeassistant:8123` | URL de Home Assistant |
| `HA_TOKEN` | — | Long-lived access token de HA |
| `EMERGENCY_PHONE` | `112` | Número de emergencias |
| `FAMILY_CONTACTS` | `[]` | JSON array de contactos familiares |

## Añadir una nueva acción

1. Crear `src/actions/mi_accion.py` con una función `async def execute(params, context) -> str`
2. El valor de retorno es el texto de respuesta al mayor
3. Registrar en `src/registry.py`: `"mi_intent": mi_accion.execute`

## Ejecutar fuera de Docker

```bash
cd services/action-controller
pip install -r requirements.txt
MOCK_ACTIONS=true MQTT_HOST=localhost HA_URL=http://localhost:8123 HA_TOKEN=xxx python -m src.main
```

## Dependencias clave

- `httpx` — llamadas a la API de Home Assistant
- `paho-mqtt` — cliente MQTT
