import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("action-controller.medication_reminder")

MEDICATION_FILE = Path("/app/data/medication.json")

DEFAULT_SCHEDULE = {
    "manana":  {"time": "09:00", "pills": []},
    "tarde":   {"time": "14:00", "pills": []},
    "noche":   {"time": "21:00", "pills": []},
}


def _load() -> dict:
    if MEDICATION_FILE.exists():
        return json.loads(MEDICATION_FILE.read_text())
    return DEFAULT_SCHEDULE


def _current_slot() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "manana"
    if hour < 18:
        return "tarde"
    return "noche"


async def execute(params: dict, context: dict) -> str:
    schedule = _load()
    slot = _current_slot()
    entry = schedule.get(slot, {})
    pills: list[str] = entry.get("pills", [])

    if not pills:
        return (
            "No tienes medicación configurada para este momento. "
            "Puedes añadirla en el panel de administración."
        )

    pills_text = ", ".join(pills[:-1]) + (" y " + pills[-1] if len(pills) > 1 else pills[0])
    return f"Tienes que tomar: {pills_text}."
