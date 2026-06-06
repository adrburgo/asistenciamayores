import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .. import alerts_store, frigate_config

router = APIRouter()
templates = Jinja2Templates(directory="/app/src/templates")

FRIGATE_URL = f"http://{os.getenv('FRIGATE_HOST', 'frigate')}:{os.getenv('FRIGATE_PORT', '5000')}"


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):  # noqa: ANN001
    collector = request.app.state.mqtt_collector
    services_status = collector.get_status()
    last_alert = collector.get_last_alert()
    recent_events = alerts_store.load()[:5]
    falls_today = alerts_store.count_today("fall")
    voice_today = alerts_store.count_today("voice")
    cameras = frigate_config.list_cameras()
    online_count = sum(1 for s in services_status.values() if s == "online")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services_status": services_status,
        "last_alert": last_alert,
        "recent_events": recent_events,
        "falls_today": falls_today,
        "voice_today": voice_today,
        "cameras_count": len(cameras),
        "online_count": online_count,
        "frigate_url": FRIGATE_URL,
        "active": "dashboard",
    })


@router.get("/api/status")
async def api_status(request: Request):  # noqa: ANN001
    collector = request.app.state.mqtt_collector
    return {
        "services": collector.get_status(),
        "last_alert": collector.get_last_alert(),
        "falls_today": alerts_store.count_today("fall"),
        "voice_today": alerts_store.count_today("voice"),
    }
