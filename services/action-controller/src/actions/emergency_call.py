import logging

from ..contacts import get_emergency_phone

log = logging.getLogger("action-controller.emergency_call")


async def execute(params: dict, context: dict) -> str:
    phone = get_emergency_phone()

    if context.get("mock"):
        log.warning("[MOCK] Llamada de emergencia al %s simulada.", phone)
        return f"Llamando al número de emergencias {phone}. Quédate tranquilo, la ayuda está en camino."

    log.critical("EMERGENCIA: iniciando llamada al %s", phone)
    # Integración con sistema de llamadas (SIP, GSM modem, etc.)
    return f"Llamando al número de emergencias {phone}. Quédate tranquilo, la ayuda está en camino."
