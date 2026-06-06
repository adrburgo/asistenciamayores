import json
import logging
import os
from pathlib import Path

log = logging.getLogger("action-controller.contacts")

CONTACTS_FILE = Path("/app/data/contacts.json")


def _default() -> dict:
    return {
        "emergency_phone": os.getenv("EMERGENCY_PHONE", "112"),
        "contacts": json.loads(os.getenv("FAMILY_CONTACTS", "[]")),
    }


def load() -> dict:
    if CONTACTS_FILE.exists():
        try:
            return json.loads(CONTACTS_FILE.read_text())
        except Exception as e:
            log.error("Error leyendo contacts.json: %s", e)
    # Primera vez: inicializar desde env vars
    data = _default()
    save(data)
    return data


def save(data: dict) -> None:
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTACTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def get_emergency_phone() -> str:
    return load().get("emergency_phone", "112")


def get_contacts() -> list[dict]:
    return load().get("contacts", [])
