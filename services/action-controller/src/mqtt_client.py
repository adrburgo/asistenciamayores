import json
import logging
from typing import Callable

import paho.mqtt.client as mqtt

log = logging.getLogger("action-controller.mqtt")


class MQTTClient:
    def __init__(self, host: str, port: int, user: str, password: str) -> None:
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.username_pw_set(user, password)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._subscriptions: dict[str, Callable[[dict], None]] = {}
        self._client.connect(host, port, keepalive=60)
        self._client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:  # noqa: ANN001
        if reason_code == 0:
            for topic in self._subscriptions:
                client.subscribe(topic)

    def _on_message(self, client, userdata, msg) -> None:  # noqa: ANN001
        handler = self._subscriptions.get(msg.topic)
        if handler:
            try:
                handler(json.loads(msg.payload.decode()))
            except Exception as e:
                log.error("Error procesando MQTT %s: %s", msg.topic, e)

    def subscribe(self, topic: str, handler: Callable[[dict], None]) -> None:
        self._subscriptions[topic] = handler
        self._client.subscribe(topic)

    def publish(self, topic: str, payload: dict) -> None:
        self._client.publish(topic, json.dumps(payload, ensure_ascii=False))

    def publish_status(self, status: str) -> None:
        self.publish("asistente/estado", {"service": "action-controller", "status": status})

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
