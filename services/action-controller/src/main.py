import asyncio
import logging
import os
import signal
from pathlib import Path

from .dispatcher import ActionDispatcher
from .mqtt_client import MQTTClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("action-controller")


async def main() -> None:
    Path("/app/data").mkdir(parents=True, exist_ok=True)

    mqtt = MQTTClient(
        host=os.environ["MQTT_HOST"],
        port=int(os.getenv("MQTT_PORT", "1883")),
        user=os.environ["MQTT_USER"],
        password=os.environ["MQTT_PASSWORD"],
    )

    context = {
        "mock": os.getenv("MOCK_ACTIONS", "false").lower() == "true",
        "emergency_phone": os.getenv("EMERGENCY_PHONE", "112"),
        "family_contacts": os.getenv("FAMILY_CONTACTS", "[]"),
        "mqtt": mqtt,
    }

    if context["mock"]:
        log.warning("Modo MOCK activado: las acciones no se ejecutarán realmente.")

    dispatcher = ActionDispatcher(context=context, mqtt=mqtt)

    def on_intent(payload: dict) -> None:
        asyncio.create_task(dispatcher.dispatch(payload))

    mqtt.subscribe("asistente/intent", on_intent)
    mqtt.publish_status("online")

    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    log.info("action-controller iniciado.")
    await stop

    mqtt.publish_status("offline")
    mqtt.disconnect()
    log.info("action-controller detenido.")


if __name__ == "__main__":
    asyncio.run(main())
