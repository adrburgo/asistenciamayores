import json
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("admin-ui.alerts")
ALERTS_FILE = Path("/app/data/alerts.json")
MAX_ENTRIES = 200


def load() -> list[dict]:
    if ALERTS_FILE.exists():
        try:
            return json.loads(ALERTS_FILE.read_text())
        except Exception as e:
            log.error("Error leyendo alerts.json: %s", e)
    return []


def append(event: dict) -> None:
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    events = load()
    events.insert(0, event)
    if len(events) > MAX_ENTRIES:
        events = events[:MAX_ENTRIES]
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERTS_FILE.write_text(json.dumps(events, ensure_ascii=False, indent=2))


def clear() -> None:
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERTS_FILE.write_text("[]")


def count_today(event_type: str | None = None) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    events = load()
    return sum(
        1 for e in events
        if e.get("timestamp", "").startswith(today)
        and (event_type is None or e.get("type") == event_type)
    )
