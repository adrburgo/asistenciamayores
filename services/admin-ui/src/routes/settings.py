import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import settings_store

log = logging.getLogger("admin-ui.settings")
router = APIRouter()
templates = Jinja2Templates(directory="/app/src/templates")

LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("pt", "Português"),
    ("ca", "Català"),
]


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):  # noqa: ANN001
    cfg = settings_store.load()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "cfg": cfg,
        "languages": LANGUAGES,
        "active": "settings",
        "saved": request.query_params.get("saved"),
    })


@router.post("/settings")
async def save_settings(
    request: Request,  # noqa: ANN001
    fall_detection_seconds: int = Form(...),
    fall_detection_confidence: float = Form(...),
    wake_word: str = Form(""),
    whisper_language: str = Form("es"),
) -> RedirectResponse:
    data = {
        "fall_detection_seconds": max(1, min(60, fall_detection_seconds)),
        "fall_detection_confidence": round(max(0.1, min(1.0, fall_detection_confidence)), 2),
        "wake_word": wake_word.strip(),
        "whisper_language": whisper_language,
    }
    settings_store.save(data)
    try:
        request.app.state.mqtt_collector.publish_config(data)
    except Exception as e:
        log.warning("No se pudo publicar config MQTT: %s", e)
    return RedirectResponse("/settings?saved=1", status_code=303)
