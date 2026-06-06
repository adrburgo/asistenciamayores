import json
import logging

log = logging.getLogger("action-controller.family_call")


async def execute(params: dict, context: dict) -> str:
    contact_name = params.get("contact_name", "").lower()

    try:
        contacts: list[dict] = json.loads(context.get("family_contacts", "[]"))
    except (json.JSONDecodeError, TypeError):
        contacts = []

    contact = next(
        (c for c in contacts if contact_name in c.get("name", "").lower()),
        contacts[0] if contacts else None,
    )

    if not contact:
        return "No tengo ningún contacto familiar configurado. Pide ayuda a tu familiar para configurarlo."

    phone = contact["phone"]
    name = contact["name"]

    if context.get("mock"):
        log.info("[MOCK] Llamada a %s (%s) simulada.", name, phone)
        return f"Llamando a {name}. Un momento por favor."

    log.info("Iniciando llamada a %s (%s)", name, phone)
    # Integración con sistema de llamadas (SIP, GSM, etc.)
    return f"Llamando a {name}. Un momento por favor."
