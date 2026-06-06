import logging

log = logging.getLogger("action-controller.home_control")

# Mapeo de palabras clave de acción a comando HA
ACTION_MAP = {
    "encender": "turn_on",
    "enciende": "turn_on",
    "apagar": "turn_off",
    "apaga": "turn_off",
    "subir": "turn_on",
    "bajar": "turn_off",
    "pon": "turn_on",
}

# Mapeo de nombre de dispositivo a entity_id de HA
DEVICE_MAP = {
    "luz": "light.salon",
    "luces": "light.salon",
    "televisión": "media_player.salon",
    "tele": "media_player.salon",
    "televisor": "media_player.salon",
    "persiana": "cover.salon",
    "persianas": "cover.salon",
    "ventilador": "switch.ventilador",
    "calefacción": "climate.salon",
}


async def execute(params: dict, context: dict) -> str:
    action_key = params.get("action", "").lower()
    device_key = params.get("device", "").lower()

    ha_action = ACTION_MAP.get(action_key)
    entity_id = DEVICE_MAP.get(device_key)

    if not ha_action or not entity_id:
        return "No he entendido qué dispositivo o acción quieres. ¿Puedes repetirlo?"

    if context.get("mock"):
        log.info("[MOCK] Publicaría home_control: %s %s", ha_action, entity_id)
        return f"De acuerdo, {action_key} el {device_key}."

    # Publica en MQTT — HA reacciona via automatización (no necesita token REST)
    mqtt = context["mqtt"]
    mqtt.publish("asistente/home_control", {
        "action": ha_action,
        "entity_id": entity_id,
        "device": device_key,
    })
    log.info("Publicado home_control: %s → %s", ha_action, entity_id)
    return f"De acuerdo, {action_key} el {device_key}."
