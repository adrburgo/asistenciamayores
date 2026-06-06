import logging
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .mqtt_status import StatusCollector
from .routes import cameras, contacts, system

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI(title="Asistencia Mayores — Panel de Administración")
app.mount("/static", StaticFiles(directory="/app/src/static"), name="static")
app.include_router(system.router)
app.include_router(cameras.router)
app.include_router(contacts.router)


@app.on_event("startup")
async def startup() -> None:
    app.state.mqtt_collector = StatusCollector(
        host=os.getenv("MQTT_HOST", "mosquitto"),
        port=int(os.getenv("MQTT_PORT", "1883")),
        user=os.getenv("MQTT_USER", ""),
        password=os.getenv("MQTT_PASSWORD", ""),
    )
