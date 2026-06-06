import logging
import os

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import frigate_config

log = logging.getLogger("admin-ui.cameras")
router = APIRouter()
templates = Jinja2Templates(directory="/app/src/templates")

FRIGATE_URL = f"http://{os.getenv('FRIGATE_HOST', 'frigate')}:{os.getenv('FRIGATE_PORT', '5000')}"


@router.get("/cameras", response_class=HTMLResponse)
async def cameras_page(request: Request):  # noqa: ANN001
    cameras = frigate_config.list_cameras()
    return templates.TemplateResponse("cameras.html", {
        "request": request,
        "cameras": cameras,
        "active": "cameras",
    })


@router.post("/cameras/add")
async def add_camera(
    name: str = Form(...),
    path: str = Form(...),
    width: int = Form(1280),
    height: int = Form(720),
    fps: int = Form(5),
):
    name_clean = name.strip().lower().replace(" ", "_")
    try:
        frigate_config.add_camera(name_clean, path.strip(), width, height, fps)
        await frigate_config.reload_frigate(FRIGATE_URL)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse("/cameras", status_code=303)


@router.post("/cameras/{name}/delete")
async def delete_camera(name: str):
    try:
        frigate_config.remove_camera(name)
        await frigate_config.reload_frigate(FRIGATE_URL)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return RedirectResponse("/cameras", status_code=303)
