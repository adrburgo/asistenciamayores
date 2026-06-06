import json
import os
from pathlib import Path

SETTINGS_FILE = Path("/app/data/settings.json")

DEFAULTS: dict = {
    "fall_detection_seconds": int(os.getenv("FALL_DETECTION_SECONDS", "5")),
    "fall_detection_confidence": float(os.getenv("FALL_DETECTION_CONFIDENCE", "0.6")),
    "wake_word": os.getenv("WAKE_WORD", ""),
    "whisper_language": os.getenv("WHISPER_LANGUAGE", "es"),
}


def load() -> dict:
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text())
            return {**DEFAULTS, **saved}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(data: dict) -> None:
    current = load()
    current.update(data)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2))
