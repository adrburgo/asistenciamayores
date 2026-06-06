import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="/app/src/templates")

FRIGATE_URL = f"http://{os.getenv('FRIGATE_HOST', 'frigate')}:{os.getenv('FRIGATE_PORT', '5000')}"
HA_URL = os.getenv("HA_URL", "http://homeassistant:8123")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):  # noqa: ANN001
    collector = request.app.state.mqtt_collector
    services_status = collector.get_status()
    last_alert = collector.get_last_alert()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services_status": services_status,
        "last_alert": last_alert,
        "frigate_url": FRIGATE_URL,
        "ha_url": HA_URL,
        "active": "dashboard",
    })


@router.get("/api/status")
async def api_status(request: Request):  # noqa: ANN001
    collector = request.app.state.mqtt_collector
    return {
        "services": collector.get_status(),
        "last_alert": collector.get_last_alert(),
    }
