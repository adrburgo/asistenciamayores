import logging
import os
import signal
import sys
import threading

from .mqtt_client import MQTTClient
from .stt import STTEngine
from .tts import TTSEngine

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("voice-service")


def main() -> None:
    mqtt = MQTTClient(
        host=os.environ["MQTT_HOST"],
        port=int(os.getenv("MQTT_PORT", "1883")),
        user=os.environ["MQTT_USER"],
        password=os.environ["MQTT_PASSWORD"],
    )
    tts = TTSEngine(
        voice=os.getenv("PIPER_VOICE", "es_ES-davefx-medium"),
        output_device=os.getenv("AUDIO_OUTPUT_DEVICE", "default"),
    )
    stt = STTEngine(
        model=os.getenv("WHISPER_MODEL", "tiny"),
        language=os.getenv("WHISPER_LANGUAGE", "es"),
        input_device=os.getenv("AUDIO_INPUT_DEVICE", "default"),
        wake_word=os.getenv("WAKE_WORD", ""),
        mqtt=mqtt,
    )

    def on_response(payload: dict) -> None:
        text = payload.get("text", "")
        if text:
            log.info("TTS: %s", text)
            stt.pause()
            tts.speak(text)
            stt.resume()

    mqtt.subscribe("asistente/respuesta", on_response)
    mqtt.publish_status("online")

    stop_event = threading.Event()

    def handle_signal(sig, frame):  # noqa: ANN001
        log.info("Señal de parada recibida.")
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    log.info("voice-service iniciado.")
    stt.start()
    stop_event.wait()

    stt.stop()
    mqtt.publish_status("offline")
    mqtt.disconnect()
    log.info("voice-service detenido.")


if __name__ == "__main__":
    main()
