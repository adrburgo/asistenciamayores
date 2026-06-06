import logging
import os
import signal
import threading

from .detector import FallDetector
from .mqtt_client import MQTTClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("vision-service")


def main() -> None:
    mqtt = MQTTClient(
        host=os.environ["MQTT_HOST"],
        port=int(os.getenv("MQTT_PORT", "1883")),
        user=os.environ["MQTT_USER"],
        password=os.environ["MQTT_PASSWORD"],
    )
    detector = FallDetector(
        frigate_host=os.getenv("FRIGATE_HOST", "frigate"),
        frigate_port=int(os.getenv("FRIGATE_PORT", "5000")),
        fall_seconds=int(os.getenv("FALL_DETECTION_SECONDS", "5")),
        confidence_threshold=float(os.getenv("FALL_DETECTION_CONFIDENCE", "0.6")),
        mqtt=mqtt,
    )

    def on_frigate_event(payload: dict) -> None:
        detector.handle_event(payload)

    mqtt.subscribe("frigate/events", on_frigate_event)
    mqtt.publish_status("online")

    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda s, f: stop_event.set())
    signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

    log.info("vision-service iniciado.")
    stop_event.wait()

    mqtt.publish_status("offline")
    mqtt.disconnect()
    log.info("vision-service detenido.")


if __name__ == "__main__":
    main()
