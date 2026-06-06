import logging

log = logging.getLogger("action-controller.emergency_call")


async def execute(params: dict, context: dict) -> str:
    phone = context.get("emergency_phone", "112")

    if context.get("mock"):
        log.warning("[MOCK] Llamada de emergencia al %s simulada.", phone)
        return f"Llamando al número de emergencias {phone}. Quédate tranquilo, la ayuda está en camino."

    log.critical("EMERGENCIA: iniciando llamada al %s", phone)
    # Aquí se integraría con el sistema de llamadas del hardware:
    # - Modem GSM via AT commands
    # - VoIP via pjsua/linphone CLI
    # - API de notificación push a la app familiar
    # Ejemplo con pjsua (requiere configuración SIP):
    # await _call_via_sip(phone)

    return f"Llamando al número de emergencias {phone}. Quédate tranquilo, la ayuda está en camino."


async def _call_via_sip(phone: str) -> None:
    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "pjsua", "--null-audio", f"sip:{phone}@emergency",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await asyncio.wait_for(proc.wait(), timeout=60)
