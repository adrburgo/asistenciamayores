import logging

from . import actions
from .actions import emergency_call, family_call, home_control, medication_reminder, status_check

log = logging.getLogger("action-controller.dispatcher")

REGISTRY: dict[str, object] = {
    "emergency_call": emergency_call.execute,
    "medication_reminder": medication_reminder.execute,
    "home_control": home_control.execute,
    "family_call": family_call.execute,
    "status_check": status_check.execute,
}


class ActionDispatcher:
    def __init__(self, context: dict, mqtt) -> None:  # noqa: ANN001
        self._context = context
        self._mqtt = mqtt

    async def dispatch(self, payload: dict) -> None:
        intent = payload.get("intent", "unknown")
        params = payload.get("params", {})
        confidence = payload.get("confidence", 0.0)

        if confidence < 0.4:
            self._respond("No he entendido bien. ¿Puedes repetirlo más despacio?")
            return

        handler = REGISTRY.get(intent)
        if handler is None:
            self._respond("No sé cómo ayudarte con eso. ¿Puedes decirlo de otra manera?")
            return

        self._mqtt.publish_status("executing")
        try:
            log.info("Ejecutando acción '%s' con params %s", intent, params)
            response_text = await handler(params=params, context=self._context)
            self._respond(response_text)
        except Exception as e:
            log.error("Error ejecutando acción '%s': %s", intent, e)
            self._respond("Ha ocurrido un problema. Por favor, inténtalo de nuevo.")
        finally:
            self._mqtt.publish_status("online")

    def _respond(self, text: str) -> None:
        self._mqtt.publish("asistente/respuesta", {"text": text})
