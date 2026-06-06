import json
import logging
from pathlib import Path

log = logging.getLogger("admin-ui.contacts")

CONTACTS_FILE = Path("/app/data/contacts.json")


def load() -> dict:
    if CONTACTS_FILE.exists():
        try:
            return json.loads(CONTACTS_FILE.read_text())
        except Exception as e:
            log.error("Error leyendo contacts.json: %s", e)
    return {"emergency_phone": "112", "contacts": []}


def save(data: dict) -> None:
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTACTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
