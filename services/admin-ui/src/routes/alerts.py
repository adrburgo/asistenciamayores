from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import alerts_store

router = APIRouter()
templates = Jinja2Templates(directory="/app/src/templates")


@router.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):  # noqa: ANN001
    events = alerts_store.load()
    falls_today = alerts_store.count_today("fall")
    voice_today = alerts_store.count_today("voice")
    return templates.TemplateResponse("alerts.html", {
        "request": request,
        "events": events,
        "falls_today": falls_today,
        "voice_today": voice_today,
        "active": "alerts",
    })


@router.post("/alerts/clear")
async def clear_alerts():
    alerts_store.clear()
    return RedirectResponse("/alerts", status_code=303)


@router.get("/api/alerts")
async def api_alerts():
    return {"events": alerts_store.load()[:30]}
