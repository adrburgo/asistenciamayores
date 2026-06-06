import logging
from pathlib import Path

import httpx
import yaml

log = logging.getLogger("admin-ui.frigate")

CONFIG_PATH = Path("/config/frigate/frigate.yml")


def _load() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text()) or {}


def _save(config: dict) -> None:
    CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))


def list_cameras() -> list[dict]:
    config = _load()
    cameras = config.get("cameras", {}) or {}
    result = []
    for name, cam_cfg in cameras.items():
        inputs = cam_cfg.get("ffmpeg", {}).get("inputs", [])
        path = inputs[0].get("path", "") if inputs else ""
        detect = cam_cfg.get("detect", {})
        result.append({
            "name": name,
            "path": path,
            "width": detect.get("width", 1280),
            "height": detect.get("height", 720),
            "fps": detect.get("fps", 5),
            "type": "usb" if path.startswith("/dev/") else "rtsp",
        })
    return result


def add_camera(name: str, path: str, width: int, height: int, fps: int) -> None:
    config = _load()
    if "cameras" not in config or config["cameras"] is None:
        config["cameras"] = {}
    if name in config["cameras"]:
        raise ValueError(f"La cámara '{name}' ya existe.")
    config["cameras"][name] = {
        "ffmpeg": {
            "inputs": [{"path": path, "roles": ["detect", "record"]}]
        },
        "detect": {"width": width, "height": height, "fps": fps},
    }
    _save(config)
    log.info("Cámara '%s' añadida.", name)


def remove_camera(name: str) -> None:
    config = _load()
    cameras = config.get("cameras") or {}
    if name not in cameras:
        raise ValueError(f"La cámara '{name}' no existe.")
    del cameras[name]
    config["cameras"] = cameras
    _save(config)
    log.info("Cámara '%s' eliminada.", name)


async def reload_frigate(frigate_url: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{frigate_url}/api/config/save", timeout=10.0)
            return resp.status_code == 200
    except Exception as e:
        log.error("No se pudo recargar Frigate: %s", e)
        return False
