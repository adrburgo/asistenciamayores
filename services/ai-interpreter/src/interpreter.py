import json
import logging
from pathlib import Path

import httpx

log = logging.getLogger("ai-interpreter.interpreter")

INTENTS_FILE = Path(__file__).parent / "intents.json"

SYSTEM_PROMPT = """Eres un clasificador de intenciones para un asistente de personas mayores.
Tu tarea es analizar lo que dice el usuario y devolver ÚNICAMENTE un JSON válido con este formato exacto:
{{"intent": "<nombre_del_intent>", "params": {{}}, "confidence": <0.0-1.0>}}

Los intents disponibles son:
{intents_description}

Reglas:
- Devuelve SOLO el JSON, sin texto adicional, sin markdown, sin explicaciones.
- Si no estás seguro, usa el intent "unknown" con confidence bajo.
- Extrae los parámetros relevantes en el campo "params" (puede estar vacío {{}}).
- La confidence debe reflejar tu certeza (0.9+ = muy seguro, 0.5-0.7 = dudoso, <0.5 = unknown).
"""


class IntentInterpreter:
    def __init__(self, ollama_host: str, ollama_port: int, model: str) -> None:
        self.model = model
        self._url = f"http://{ollama_host}:{ollama_port}/api/chat"
        self._intents = self._load_intents()
        self._system_prompt = self._build_system_prompt()

    def _load_intents(self) -> dict:
        return json.loads(INTENTS_FILE.read_text(encoding="utf-8"))

    def _build_system_prompt(self) -> str:
        descriptions = []
        for name, info in self._intents.items():
            examples = ", ".join(f'"{e}"' for e in info["examples"][:3])
            descriptions.append(f'- "{name}": {info["description"]}  Ejemplos: {examples}')
        return SYSTEM_PROMPT.format(intents_description="\n".join(descriptions))

    def classify(self, text: str) -> dict:
        try:
            response = httpx.post(
                self._url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self._system_prompt},
                        {"role": "user", "content": text},
                    ],
                    "stream": False,
                    "format": "json",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            result = json.loads(content)
            if "intent" not in result or result["intent"] not in self._intents:
                result["intent"] = "unknown"
                result.setdefault("confidence", 0.0)
            result.setdefault("params", {})
            return result
        except Exception as e:
            log.error("Error clasificando intent: %s", e)
            return {"intent": "unknown", "params": {}, "confidence": 0.0}
