# Sistema de Asistencia para Mayores

Sistema offline de asistencia para personas mayores que corre en un miniordenador. Detecta caídas por cámara y permite al mayor controlar el hogar, pedir ayuda de emergencia y gestionar recordatorios de medicación mediante voz.

Todo funciona **sin conexión a internet**. Los servicios se comunican internamente por MQTT y se orquestan con Docker Compose.

## Características

- **Asistente de voz** — El mayor habla, Whisper transcribe y un LLM local (Ollama) interpreta la intención y ejecuta la acción
- **Detección de caídas** — Cámaras gestionadas por Frigate + YOLOv8-Pose para detectar si la persona está tumbada
- **Panel de administración** — Interfaz web (`:8080`) para añadir cámaras y ver el estado del sistema
- **Home Assistant** — Dashboard, alertas y automatizaciones del hogar
- **Auto-arranque** — El sistema se inicia automáticamente al encender el dispositivo

## Arquitectura

Ver [CONTEXT_MAIN.md](CONTEXT_MAIN.md) para el diagrama completo de servicios y tópicos MQTT.

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Mosquitto (MQTT) | 1883 | Bus de mensajes interno |
| Ollama | 11434 | Servidor LLM local |
| Home Assistant | 8123 | Dashboard y automatizaciones |
| Frigate | 5000 | NVR + detección de personas |
| **admin-ui** | **8080** | Panel de gestión de cámaras y estado |
| voice-service | — | Whisper STT + Piper TTS |
| ai-interpreter | — | Clasificación de intents |
| action-controller | — | Ejecución de acciones |
| vision-service | — | Detección de caídas YOLOv8-Pose |

## Requisitos

- Docker Engine ≥ 24 y Docker Compose v2
- Linux (probado en Arch/Ubuntu); requiere acceso a `/dev/snd` para audio y `/dev/bus/usb` para cámaras USB
- 4 GB RAM mínimo (8 GB recomendado para modelos medianos)
- Python 3.12 (solo para desarrollo local fuera de Docker)

## Puesta en marcha

### 1. Clonar y configurar

```bash
git clone <url-del-repo>
cd asistenciamayores

# Copiar y editar ficheros de configuración
cp .env.example .env
cp config/homeassistant/secrets.yaml.example config/homeassistant/secrets.yaml
```

Editar `.env` con los valores reales:

| Variable | Descripción |
|----------|-------------|
| `MQTT_PASSWORD` | Contraseña del broker MQTT |
| `EMERGENCY_PHONE` | Número de teléfono para alertas SOS |
| `FAMILY_CONTACTS` | JSON con contactos: `'[{"name":"...", "phone":"..."}]'` |

### 2. Setup inicial (una sola vez)

```bash
./scripts/setup.sh
```

Crea el fichero de contraseñas MQTT y descarga el modelo Ollama.

### 3. Arrancar

**Desarrollo** (logs en consola, hot-reload, acciones mock):
```bash
./scripts/start-dev.sh
```

**Producción** (background, restart automático):
```bash
./scripts/start-prod.sh
```

### 4. Auto-arranque al encender (producción)

```bash
sudo ./scripts/install-service.sh
```

Instala un servicio systemd que arranca el sistema automáticamente con el miniordenador.

### 5. Acceder

| Servicio | URL |
|----------|-----|
| Panel de administración | `http://localhost:8080` |
| Home Assistant | `http://localhost:8123` |
| Frigate (cámaras) | `http://localhost:5000` |

## Desarrollo

### Estructura del proyecto

```
services/
├── voice-service/      # Whisper STT + Piper TTS
├── ai-interpreter/     # Clasificación de intents con Ollama
├── action-controller/  # Ejecución de acciones predefinidas
├── vision-service/     # Detección de caídas YOLOv8-Pose
└── admin-ui/           # Panel web FastAPI
config/
├── homeassistant/      # Configuración de HA
├── frigate/            # Configuración de cámaras
├── mosquitto/          # Broker MQTT
└── ollama/             # Scripts de descarga de modelos
```

Cada servicio tiene su propio `CONTEXT.md` con detalles de implementación, tópicos MQTT y variables de entorno.

### Añadir una nueva acción de voz

1. Añadir el intent en [`services/ai-interpreter/src/intents.json`](services/ai-interpreter/src/intents.json) con ejemplos de frases
2. Crear `services/action-controller/src/actions/<nombre>.py` con una función `async def execute(params, context) -> str`
3. Registrar en [`services/action-controller/src/dispatcher.py`](services/action-controller/src/dispatcher.py)

### Añadir una cámara

Desde el panel web en `http://localhost:8080/cameras` (sin editar YAML).

### Variables de entorno por servicio

Cada servicio lee sus variables del `.env` via Docker Compose. Ver [`docker-compose.yml`](docker-compose.yml) para la lista completa por servicio.

### Modo desarrollo sin Docker (un servicio)

```bash
cd services/ai-interpreter
pip install -r requirements.txt
OLLAMA_HOST=localhost MQTT_HOST=localhost OLLAMA_MODEL=llama3.2:3b python -m src.main
```

## Gestión del sistema

```bash
# Ver estado de todos los contenedores
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Reiniciar un servicio concreto
docker compose restart vision-service

# Parar todo
docker compose down

# Con systemd (producción)
sudo systemctl status asistenciamayores
sudo journalctl -u asistenciamayores -f
```

## Seguridad

- El fichero `.env` y `config/homeassistant/secrets.yaml` **nunca se commitean** (están en `.gitignore`)
- Copiar siempre desde los ficheros `.example` correspondientes
- El broker MQTT requiere autenticación; la contraseña se genera en el setup
- Todos los servicios corren en una red Docker interna aislada (`asistente_net`)
