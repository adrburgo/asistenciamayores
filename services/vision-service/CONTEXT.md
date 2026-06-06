# vision-service

## Propósito

Detecta caídas de personas analizando frames de las cámaras gestionadas por Frigate. Usa dos capas:

1. **Frigate** detecta presencia de personas y publica eventos en MQTT (`frigate/events`)
2. **vision-service** recibe esos eventos, descarga el snapshot del frame desde la API de Frigate y aplica **YOLOv8n-Pose** para estimar la postura corporal. Si los keypoints indican que la persona está tumbada durante N segundos consecutivos, lanza una alerta de caída.

## Lógica de detección de caída

Una persona se considera "tumbada" cuando:
- La relación entre la altura del bounding box y su anchura es `< 0.6` (persona horizontal)
- O los keypoints de hombros/caderas están a una altura similar a los keypoints de rodillas/tobillos (delta_y < 20% de la altura de la imagen)

La alerta solo se lanza si la condición se mantiene durante `FALL_DETECTION_SECONDS` (default: 5s) para evitar falsos positivos por agacharse.

## Tópicos MQTT

| Tópico | Tipo | Contenido |
|--------|------|-----------|
| `frigate/events` | Suscribe | Eventos de detección de Frigate |
| `caidas/alerta` | Publica | `{"camera": "...", "timestamp": "...", "confidence": 0.8}` |
| `caidas/persona_detectada` | Publica | `{"camera": "...", "pose": "standing/lying", "timestamp": "..."}` |
| `caidas/estado` | Publica | `{"status": "online/offline"}` |

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `FRIGATE_HOST` | `frigate` | Host de Frigate |
| `FRIGATE_PORT` | `5000` | Puerto de la API de Frigate |
| `FALL_DETECTION_SECONDS` | `5` | Segundos para confirmar caída |
| `FALL_DETECTION_CONFIDENCE` | `0.6` | Confianza mínima para alerta |

## Modelo YOLOv8-Pose

El modelo `yolov8n-pose.pt` se descarga automáticamente de Ultralytics al primer inicio y se persiste en el volumen `yolo_models`. En hardware limitado usar `yolov8n-pose` (nano); en hardware más potente usar `yolov8s-pose`.

## Ejecutar fuera de Docker

```bash
cd services/vision-service
pip install -r requirements.txt
FRIGATE_HOST=localhost MQTT_HOST=localhost python -m src.main
```

## Dependencias clave

- `ultralytics` — YOLOv8-Pose
- `httpx` — descarga snapshots de Frigate
- `Pillow` / `numpy` — procesamiento de imágenes
- `paho-mqtt` — cliente MQTT
