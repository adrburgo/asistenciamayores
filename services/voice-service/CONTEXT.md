# voice-service

## Propósito

Captura audio del micrófono, transcribe con **Whisper** (faster-whisper, offline) y publica el texto en MQTT. También escucha respuestas en `asistente/respuesta` y las sintetiza con **Piper TTS** para reproducirlas por el altavoz.

## Flujo

```
Micrófono → silero-vad (detección de voz) → faster-whisper (STT)
→ MQTT: asistente/texto

MQTT: asistente/respuesta → piper-tts (TTS) → altavoz
```

Si `WAKE_WORD` está configurado, el servicio usa **openWakeWord** para activarse solo cuando el mayor pronuncia la palabra clave. Si está vacío, escucha continuamente.

## Tópicos MQTT

| Tópico | Tipo | Contenido |
|--------|------|-----------|
| `asistente/texto` | Publica | `{"text": "...", "timestamp": "...", "confidence": 0.95}` |
| `asistente/respuesta` | Suscribe | `{"text": "..."}` |
| `asistente/estado` | Publica | `{"status": "online/offline/listening/speaking"}` |

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `WHISPER_MODEL` | `tiny` | Modelo Whisper (tiny/base/small/medium) |
| `WHISPER_LANGUAGE` | `es` | Idioma de transcripción |
| `AUDIO_INPUT_DEVICE` | `default` | Dispositivo ALSA de entrada |
| `AUDIO_OUTPUT_DEVICE` | `default` | Dispositivo ALSA de salida |
| `WAKE_WORD` | `` | Palabra clave de activación (vacío = siempre activo) |
| `PIPER_VOICE` | `es_ES-davefx-medium` | Voz de Piper TTS |

## Modelos

- Whisper se descarga automáticamente al primer inicio desde Hugging Face
- Los modelos se persisten en el volumen Docker `whisper_models`
- Piper descarga la voz configurada automáticamente

## Ejecutar fuera de Docker (desarrollo)

```bash
cd services/voice-service
pip install -r requirements.txt
WHISPER_MODEL=tiny MQTT_HOST=localhost python -m src.main
```

## Dependencias clave

- `faster-whisper` — STT offline eficiente
- `silero-vad` — detección de actividad de voz
- `piper-tts` — TTS offline en español
- `pyaudio` / `sounddevice` — captura/reproducción de audio
- `paho-mqtt` — cliente MQTT
