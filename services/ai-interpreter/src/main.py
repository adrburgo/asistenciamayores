import logging
import os
import signal
import threading

from .interpreter import IntentInterpreter
from .mqtt_client import MQTTClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("ai-interpreter")


def main() -> None:
    mqtt = MQTTClient(
        host=os.environ["MQTT_HOST"],
        port=int(os.getenv("MQTT_PORT", "1883")),
        user=os.environ["MQTT_USER"],
        password=os.environ["MQTT_PASSWORD"],
    )
    interpreter = IntentInterpreter(
        ollama_host=os.getenv("OLLAMA_HOST", "ollama"),
        ollama_port=int(os.getenv("OLLAMA_PORT", "11434")),
        model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
    )

    def on_text(payload: dict) -> None:
        text = payload.get("text", "").strip()
        if not text:
            return
        log.info("Texto recibido: %s", text)
        mqtt.publish_status("processing")
        result = interpreter.classify(text)
        result["original_text"] = text
        log.info("Intent: %s (confianza: %.2f)", result["intent"], result.get("confidence", 0))
        mqtt.publish("asistente/intent", result)
        mqtt.publish_status("online")

    mqtt.subscribe("asistente/texto", on_text)
    mqtt.publish_status("online")

    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda s, f: stop_event.set())
    signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

    log.info("ai-interpreter iniciado con modelo '%s'.", interpreter.model)
    stop_event.wait()

    mqtt.publish_status("offline")
    mqtt.disconnect()
    log.info("ai-interpreter detenido.")


if __name__ == "__main__":
    main()
