# ai-interpreter

## Propósito

Recibe texto transcrito en `asistente/texto`, lo envía al LLM local (Ollama) para clasificar la intención del usuario y publica el intent resultante en `asistente/intent`.

Usa un **prompt de sistema** estricto que obliga al LLM a responder siempre con un JSON válido con los campos `intent`, `params` y `confidence`. Los intents posibles se definen en `src/intents.json`.

## Flujo

```
MQTT: asistente/texto → Ollama API (HTTP) → clasificación → MQTT: asistente/intent
```

## Tópicos MQTT

| Tópico | Tipo | Contenido |
|--------|------|-----------|
| `asistente/texto` | Suscribe | `{"text": "...", "timestamp": "..."}` |
| `asistente/intent` | Publica | `{"intent": "...", "params": {...}, "confidence": 0.9, "original_text": "..."}` |
| `asistente/estado` | Publica | `{"status": "online/offline/processing"}` |

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2:3b` | Modelo a usar |
| `OLLAMA_HOST` | `ollama` | Host del servidor Ollama |
| `OLLAMA_PORT` | `11434` | Puerto de Ollama |

## Extender con nuevos intents

Editar `src/intents.json`:
```json
{
  "nuevo_intent": {
    "description": "Descripción de la acción",
    "examples": ["frase de ejemplo 1", "frase de ejemplo 2"],
    "params": ["param1"]
  }
}
```

No es necesario recompilar ni reiniciar si el servicio detecta cambios en el fichero (hot-reload en dev).

## Ejecutar fuera de Docker

```bash
cd services/ai-interpreter
pip install -r requirements.txt
OLLAMA_MODEL=llama3.2:3b OLLAMA_HOST=localhost MQTT_HOST=localhost python -m src.main
```

## Dependencias clave

- `httpx` — cliente HTTP para Ollama API
- `paho-mqtt` — cliente MQTT
