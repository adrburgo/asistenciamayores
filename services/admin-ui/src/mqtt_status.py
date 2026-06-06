import json
import logging
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from . import alerts_store

log = logging.getLogger("admin-ui.mqtt")

WATCHED_SERVICES = ["voice-service", "ai-interpreter", "action-controller", "vision-service"]


class StatusCollector:
    def __init__(self, host: str, port: int, user: str, password: str) -> None:
        self._status: dict[str, str] = {s: "unknown" for s in WATCHED_SERVICES}
        self._last_alert: dict | None = None
        self._lock = threading.Lock()

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.username_pw_set(user, password)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        try:
            self._client.connect(host, port, keepalive=30)
            self._client.loop_start()
        except Exception as e:
            log.warning("No se pudo conectar al broker MQTT: %s", e)

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:  # noqa: ANN001
        if reason_code == 0:
            client.subscribe("asistente/estado")
            client.subscribe("caidas/estado")
            client.subscribe("caidas/alerta")
            client.subscribe("asistente/respuesta")
            client.subscribe("asistente/texto")
            log.info("MQTT conectado y suscrito.")

    def _on_message(self, client, userdata, msg) -> None:  # noqa: ANN001
        try:
            payload = json.loads(msg.payload.decode())
            now = datetime.now(timezone.utc).isoformat()
            with self._lock:
                if msg.topic in ("asistente/estado", "caidas/estado"):
                    service = payload.get("service", "")
                    status = payload.get("status", "unknown")
                    if service:
                        self._status[service] = status

                elif msg.topic == "caidas/alerta":
                    self._last_alert = payload
                    alerts_store.append({
                        "type": "fall",
                        "camera": payload.get("camera", "desconocida"),
                        "confidence": payload.get("confidence", 0),
                        "timestamp": payload.get("timestamp", now),
                    })

                elif msg.topic == "asistente/respuesta":
                    alerts_store.append({
                        "type": "action",
                        "action": payload.get("text", ""),
                        "detail": "",
                        "timestamp": now,
                    })

                elif msg.topic == "asistente/texto":
                    alerts_store.append({
                        "type": "voice",
                        "text": payload.get("text", ""),
                        "timestamp": payload.get("timestamp", now),
                    })

        except Exception as e:
            log.debug("Error procesando MQTT: %s", e)

    def publish_config(self, config: dict) -> None:
        try:
            self._client.publish(
                "config/asistente",
                json.dumps(config, ensure_ascii=False),
                retain=True,
            )
        except Exception as e:
            log.warning("Error publicando config: %s", e)

    def get_status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def get_last_alert(self) -> dict | None:
        with self._lock:
            return self._last_alert
