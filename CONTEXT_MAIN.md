# Sistema de Asistencia para Mayores — Contexto Principal

## ¿Qué es este proyecto?

Sistema offline de asistencia para personas mayores que corre en un miniordenador. Tiene dos funciones principales:

1. **Asistente de voz**: El mayor habla, el sistema transcribe con Whisper, un LLM local (Ollama) interpreta la intención y un controlador ejecuta la acción predefinida correspondiente (SOS, recordatorio, control del hogar, videollamada familiar).

2. **Detección de caídas**: Cámaras gestionadas por Frigate detectan personas. Un servicio Python aplica estimación de pose (YOLOv8-Pose) para identificar si la persona está tumbada. Si es así, lanza una alerta a Home Assistant.

Todo funciona **100% offline**. Los servicios se comunican por **MQTT (Mosquitto)**. Home Assistant actúa como panel de control y motor de automatizaciones.

3. **Panel de administración** (`admin-ui`): Interfaz web en `:8080` para gestionar cámaras (añadir/eliminar RTSP o USB) y monitorizar el estado de todos los servicios en tiempo real.

4. **Auto-arranque**: Un servicio systemd arranca automáticamente el stack Docker al encender el mini-ordenador.

---

## Diagrama de servicios

```
                    ┌─────────────────────────────────────────────┐
                    │              MQTT (Mosquitto :1883)          │
                    └───────────┬──────────┬────────┬─────────────┘
                                │          │        │
        ┌───────────────────────┼──────────┼────────┼───────────────────────┐
        │                       │          │        │                       │
        ▼                       ▼          ▼        ▼                       ▼
┌──────────────┐  ┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐
│voice-service │  │ ai-interpreter  │  │action-controller│  │ vision-service   │
│              │  │                 │  │                 │  │                  │
│ Micrófono    │  │ Ollama LLM      │  │ SOS / llamadas  │  │ YOLOv8-Pose      │
│ Whisper STT  │  │ Intent classify │  │ Recordatorios   │  │ Detección caídas │
│ Piper TTS    │  │                 │  │ Domótica (HA)   │  │                  │
└──────────────┘  └─────────────────┘  └────────────────┘  └──────────────────┘
        │                  ▲                    │                   │
        │ asistente/texto  │                    │ asistente/        │ caidas/
        └──────────────────┘                    │ respuesta         │ alerta
                                                │                   │
                    ┌───────────────────────────┼───────────────────┘
                    │                           │
                    ▼                           ▼
        ┌────────────────────┐    ┌─────────────────────────┐
        │   Home Assistant   │    │         Frigate          │
        │   :8123            │◄───┤   :5000 / :8971          │
        │   Dashboard, alertas│   │   NVR + person detect   │
        │   automatizaciones │    │   Streams RTSP/USB cam  │
        └────────────────────┘    └─────────────────────────┘
                    ▲
                    │
        ┌───────────────────┐
        │      Ollama       │
        │      :11434       │
        │  LLM local server │
        └───────────────────┘
```

---

## Tópicos MQTT

| Tópico | Publicado por | Consumido por | Contenido |
|--------|--------------|---------------|-----------|
| `asistente/texto` | voice-service | ai-interpreter | Texto transcrito por Whisper |
| `asistente/intent` | ai-interpreter | action-controller | JSON `{intent, params, confidence}` |
| `asistente/respuesta` | action-controller | voice-service | Texto para responder al mayor via TTS |
| `asistente/estado` | todos | homeassistant | JSON de estado del servicio |
| `caidas/alerta` | vision-service | homeassistant | JSON `{camera, timestamp, confidence}` |
| `caidas/persona_detectada` | vision-service | homeassistant | JSON `{camera, pose, timestamp}` |
| `frigate/events` | frigate | vision-service | Eventos de detección de Frigate |
| `homeassistant/status` | homeassistant | todos | Estado de HA (online/offline) |

---

## Intents del asistente

Definidos en `services/ai-interpreter/src/intents.json`. Extensibles sin tocar código.

| Intent | Ejemplo de frase | Acción |
|--------|-----------------|--------|
| `emergency_call` | "Ayuda", "Llama al médico", "Emergencia" | Llama al número de emergencias configurado |
| `medication_reminder` | "¿Qué pastillas tomo hoy?", "Recuérdame la medicación" | Consulta/crea recordatorio en HA |
| `home_control` | "Enciende la luz", "Apaga la televisión" | Llama al servicio de HA correspondiente |
| `family_call` | "Llama a mi hijo", "Quiero hablar con María" | Inicia llamada al contacto configurado |
| `status_check` | "¿Todo bien?", "¿Cómo estoy?" | Responde con estado del sistema |
| `unknown` | Cualquier otra frase | Pide aclaración al mayor |

---

## Modos de ejecución

### Desarrollo
```bash
./scripts/start-dev.sh
# o:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```
- Modelos pequeños: `whisper-tiny` + `llama3.2:3b`
- Hot-reload en servicios Python
- `action-controller` en modo mock (no ejecuta llamadas reales)
- Logs verbose en consola

### Producción
```bash
./scripts/start-prod.sh
# o:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
- Modelos: `whisper-tiny` + `llama3.2:3b` (igual que desarrollo)
- `restart: always` en todos los servicios
- Healthchecks con auto-recovery
- Logs a archivo en `./logs/`

---

## Cómo añadir una nueva acción al asistente

1. Añadir el intent en `services/ai-interpreter/src/intents.json` con ejemplos de frases
2. Añadir el handler en `services/action-controller/src/actions/` (un fichero Python por acción)
3. Registrar el handler en `services/action-controller/src/registry.py`
4. (Opcional) Añadir automatización en `config/homeassistant/automations.yaml`

---

## Cómo añadir una nueva cámara

Desde el panel web `http://<ip>:8080/cameras` (sin editar YAML).
O manualmente: editar `config/frigate/frigate.yml` → sección `cameras` y reiniciar Frigate con `docker compose restart frigate`.

---

## Variables de entorno principales

Ver `.env.example` para la lista completa. Las críticas son:

| Variable | Descripción |
|----------|-------------|
| `EMERGENCY_PHONE` | Número de teléfono para alertas SOS |
| `FAMILY_CONTACTS` | JSON con contactos familiares `'[{"name":"...","phone":"..."}]'` |
| `MQTT_HOST` | Host del broker MQTT (default: `mosquitto`) |
| `MQTT_PASSWORD` | Contraseña del broker MQTT |
| `OLLAMA_MODEL_DEV` | Modelo Ollama para desarrollo (default: `llama3.2:3b`) |
| `OLLAMA_MODEL_PROD` | Modelo Ollama para producción (default: `llama3.2:3b`) |
| `WHISPER_MODEL_DEV` | Modelo Whisper para desarrollo (default: `tiny`) |
| `WHISPER_MODEL_PROD` | Modelo Whisper para producción (default: `tiny`) |
| `HA_URL` | URL de Home Assistant, solo para el enlace en admin-ui (default: `http://homeassistant:8123`) |

---

## Secciones del proyecto

Cada servicio tiene su propio `CONTEXT.md`:

- [services/voice-service/CONTEXT.md](services/voice-service/CONTEXT.md) — STT/TTS con Whisper y Piper
- [services/ai-interpreter/CONTEXT.md](services/ai-interpreter/CONTEXT.md) — Clasificación de intents con Ollama
- [services/action-controller/CONTEXT.md](services/action-controller/CONTEXT.md) — Ejecución de acciones predefinidas
- [services/vision-service/CONTEXT.md](services/vision-service/CONTEXT.md) — Detección de caídas con YOLOv8-Pose
- [services/admin-ui/CONTEXT.md](services/admin-ui/CONTEXT.md) — Panel web: gestión de cámaras y monitorización

---

## Auto-arranque con el sistema

Para que el stack arranque automáticamente al encender el mini-ordenador:

```bash
# Copiar el proyecto a /opt y registrar el servicio systemd
sudo ./scripts/install-service.sh
```

Esto instala `systemd/asistenciamayores.service` en `/etc/systemd/system/` y lo habilita con `systemctl enable`. A partir de ese momento, al encender el dispositivo se lanza automáticamente `docker compose up -d` en modo producción.

Comandos de gestión:
```bash
sudo systemctl status  asistenciamayores   # Ver estado
sudo systemctl restart asistenciamayores   # Reiniciar
sudo systemctl stop    asistenciamayores   # Parar
sudo journalctl -u     asistenciamayores -f # Ver logs en tiempo real
```
