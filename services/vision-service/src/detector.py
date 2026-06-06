import io
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import numpy as np
from PIL import Image
from ultralytics import YOLO

log = logging.getLogger("vision-service.detector")

MODEL_DIR = Path("/app/models")
MODEL_NAME = "yolov8n-pose.pt"

# Keypoint indices en YOLOv8-Pose (COCO 17 keypoints)
KP_LEFT_SHOULDER = 5
KP_RIGHT_SHOULDER = 6
KP_LEFT_HIP = 11
KP_RIGHT_HIP = 12
KP_LEFT_KNEE = 13
KP_RIGHT_KNEE = 14
KP_LEFT_ANKLE = 15
KP_RIGHT_ANKLE = 16


class FallDetector:
    def __init__(
        self,
        frigate_host: str,
        frigate_port: int,
        fall_seconds: int,
        confidence_threshold: float,
        mqtt,  # noqa: ANN001
    ) -> None:
        self._frigate_base = f"http://{frigate_host}:{frigate_port}"
        self._fall_seconds = fall_seconds
        self._confidence_threshold = confidence_threshold
        self._mqtt = mqtt
        self._lying_since: dict[str, float] = {}

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        log.info("Cargando modelo YOLOv8n-Pose...")
        self._model = YOLO(str(MODEL_DIR / MODEL_NAME))
        log.info("Modelo cargado.")

    def handle_event(self, payload: dict) -> None:
        event_type = payload.get("type")
        camera = payload.get("after", {}).get("camera") or payload.get("before", {}).get("camera")
        event_id = payload.get("after", {}).get("id")

        if event_type not in ("new", "update") or not camera or not event_id:
            return
        if payload.get("after", {}).get("label") != "person":
            return

        frame = self._fetch_snapshot(camera, event_id)
        if frame is None:
            return

        pose = self._analyze_pose(frame)
        self._mqtt.publish("caidas/persona_detectada", {
            "camera": camera,
            "pose": pose,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if pose == "lying":
            if camera not in self._lying_since:
                self._lying_since[camera] = time.monotonic()
                log.info("Persona tumbada detectada en cámara %s. Iniciando contador.", camera)
            elif time.monotonic() - self._lying_since[camera] >= self._fall_seconds:
                self._trigger_fall_alert(camera)
        else:
            if camera in self._lying_since:
                log.debug("Persona se ha levantado en cámara %s. Reseteando contador.", camera)
                del self._lying_since[camera]

    def _fetch_snapshot(self, camera: str, event_id: str) -> np.ndarray | None:
        try:
            resp = httpx.get(
                f"{self._frigate_base}/api/events/{event_id}/snapshot.jpg",
                timeout=5.0,
            )
            resp.raise_for_status()
            image = Image.open(io.BytesIO(resp.content)).convert("RGB")
            return np.array(image)
        except Exception as e:
            log.warning("No se pudo obtener snapshot del evento %s: %s", event_id, e)
            return None

    def _analyze_pose(self, frame: np.ndarray) -> str:
        results = self._model(frame, verbose=False)
        if not results or results[0].keypoints is None:
            return "unknown"

        for keypoints in results[0].keypoints.xy:
            kp = keypoints.cpu().numpy()
            if len(kp) < 17:
                continue

            img_height = frame.shape[0]
            pose = _classify_pose(kp, img_height)
            if pose == "lying":
                return "lying"

        return "standing"

    def _trigger_fall_alert(self, camera: str) -> None:
        log.warning("ALERTA DE CAÍDA detectada en cámara %s", camera)
        self._mqtt.publish("caidas/alerta", {
            "camera": camera,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": self._confidence_threshold,
            "alert": True,
        })
        # Reset para evitar alertas repetidas en el mismo evento
        self._lying_since.pop(camera, None)


def _classify_pose(kp: np.ndarray, img_height: int) -> str:
    """Determina si la persona está tumbada basándose en keypoints de pose."""
    def valid(idx: int) -> bool:
        return kp[idx][0] > 0 and kp[idx][1] > 0

    # Método 1: ratio del bounding box (persona tumbada → ancho >> alto)
    visible = kp[kp[:, 0] > 0]
    if len(visible) >= 4:
        y_range = visible[:, 1].max() - visible[:, 1].min()
        x_range = visible[:, 0].max() - visible[:, 0].min()
        if x_range > 0 and y_range / x_range < 0.5:
            return "lying"

    # Método 2: diferencia vertical entre hombros/caderas y rodillas/tobillos
    upper_indices = [KP_LEFT_SHOULDER, KP_RIGHT_SHOULDER, KP_LEFT_HIP, KP_RIGHT_HIP]
    lower_indices = [KP_LEFT_KNEE, KP_RIGHT_KNEE, KP_LEFT_ANKLE, KP_RIGHT_ANKLE]

    upper_ys = [kp[i][1] for i in upper_indices if valid(i)]
    lower_ys = [kp[i][1] for i in lower_indices if valid(i)]

    if upper_ys and lower_ys:
        avg_upper_y = sum(upper_ys) / len(upper_ys)
        avg_lower_y = sum(lower_ys) / len(lower_ys)
        vertical_diff = abs(avg_lower_y - avg_upper_y)
        # Si la diferencia vertical es menor al 20% de la altura de la imagen → tumbado
        if vertical_diff < img_height * 0.20:
            return "lying"

    return "standing"
