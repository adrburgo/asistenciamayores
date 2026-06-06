import logging
from datetime import datetime

import httpx

log = logging.getLogger("action-controller.status_check")

DAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


async def execute(params: dict, context: dict) -> str:
    query_type = params.get("query_type", "general")
    now = datetime.now()

    if "hora" in query_type or "hora" in str(params).lower():
        return f"Son las {now.strftime('%H:%M')}."

    if "día" in query_type or "fecha" in query_type:
        day_name = DAYS_ES[now.weekday()]
        month_name = MONTHS_ES[now.month - 1]
        return f"Hoy es {day_name}, {now.day} de {month_name} de {now.year}."

    if "tiempo" in query_type or "clima" in query_type:
        return "Lo siento, no tengo acceso a información del tiempo."

    return (
        f"Son las {now.strftime('%H:%M')} del {DAYS_ES[now.weekday()]}, "
        f"{now.day} de {MONTHS_ES[now.month - 1]}. "
        "El sistema funciona correctamente."
    )
