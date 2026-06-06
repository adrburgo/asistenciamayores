import logging

from ..contacts import get_contacts

log = logging.getLogger("action-controller.family_call")


async def execute(params: dict, context: dict) -> str:
    contact_name = params.get("contact_name", "").lower()
    contacts = get_contacts()

    contact = next(
        (c for c in contacts if contact_name in c.get("name", "").lower()),
        contacts[0] if contacts else None,
    )

    if not contact:
        return "No tengo ningún contacto familiar configurado. Puedes añadirlos en el panel de administración."

    phone = contact["phone"]
    name = contact["name"]

    if context.get("mock"):
        log.info("[MOCK] Llamada a %s (%s) simulada.", name, phone)
        return f"Llamando a {name}. Un momento por favor."

    log.info("Iniciando llamada a %s (%s)", name, phone)
    return f"Llamando a {name}. Un momento por favor."
