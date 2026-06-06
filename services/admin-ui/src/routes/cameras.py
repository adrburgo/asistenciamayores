import asyncio
import logging
import os
import subprocess
from pathlib import Path

import httpx
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates

from .. import frigate_config

log = logging.getLogger("admin-ui.cameras")
router = APIRouter()
templates = Jinja2Templates(directory="/app/src/templates")

FRIGATE_URL = f"http://{os.getenv('FRIGATE_HOST', 'frigate')}:{os.getenv('FRIGATE_PORT', '5000')}"
V4L_PATH = Path("/sys/class/video4linux")


def _scan_usb_devices() -> list[dict]:
    devices = []
    if not V4L_PATH.exists():
        return devices
    for dev_dir in sorted(V4L_PATH.iterdir(), key=lambda p: p.name):
        try:
            index = int((dev_dir / "index").read_text().strip())
        except Exception:
            index = 0
        if index != 0:
            continue
        try:
            name = (dev_dir / "name").read_text().strip()
        except Exception:
            name = dev_dir.name
        devices.append({
            "path": f"/dev/{dev_dir.name}",
            "label": f"{name} ({dev_dir.name})",
        })
    return devices


@router.get("/api/cameras/scan")
async def scan_cameras():
    return {"devices": _scan_usb_devices()}


@router.get("/api/cameras/capture")
async def capture_device(path: str):
    """Captura un frame directo de un dispositivo V4L2 via ffmpeg."""
    dev = Path(path)
    if not str(dev).startswith("/dev/video"):
        raise HTTPException(status_code=400, detail="Ruta de dispositivo no válida")
    if not dev.exists():
        raise HTTPException(status_code=404, detail=f"{path} no encontrado en el contenedor")
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            [
                "ffmpeg", "-y",
                "-f", "v4l2",
                "-input_format", "mjpeg",
                "-i", str(dev),
                "-vframes", "1",
                "-q:v", "5",
                "-f", "image2", "pipe:1",
            ],
            capture_output=True,
            timeout=8,
        )
        if result.returncode == 0 and result.stdout:
            return Response(content=result.stdout, media_type="image/jpeg")
        # Reintento sin forzar mjpeg (algunas webcams usan yuyv)
        result2 = await asyncio.to_thread(
            subprocess.run,
            ["ffmpeg", "-y", "-f", "v4l2", "-i", str(dev),
             "-vframes", "1", "-q:v", "5", "-f", "image2", "pipe:1"],
            capture_output=True,
            timeout=8,
        )
        if result2.returncode == 0 and result2.stdout:
            return Response(content=result2.stdout, media_type="image/jpeg")
        raise HTTPException(status_code=500, detail="ffmpeg no pudo capturar imagen")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout capturando imagen") from None


@router.get("/cameras/{name}/snapshot")
async def camera_snapshot(name: str):
    """Proxy del último snapshot de Frigate."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{FRIGATE_URL}/api/{name}/latest.jpg",
                params={"bbox": 1},
                timeout=5.0,
            )
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="image/jpeg")
        raise HTTPException(status_code=resp.status_code, detail="Frigate no responde")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Frigate no disponible") from e


@router.get("/cameras/{name}/stream")
async def camera_stream(name: str):
    """Proxy del stream MJPEG de Frigate."""
    async def _generate():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "GET", f"{FRIGATE_URL}/api/{name}/stream"
                ) as resp:
                    async for chunk in resp.aiter_bytes(4096):
                        yield chunk
        except Exception as e:
            log.warning("Stream interrumpido para %s: %s", name, e)

    return StreamingResponse(
        _generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/cameras", response_class=HTMLResponse)
async def cameras_page(request: Request):  # noqa: ANN001
    cameras = frigate_config.list_cameras()
    return templates.TemplateResponse("cameras.html", {
        "request": request,
        "cameras": cameras,
        "frigate_url": FRIGATE_URL,
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
