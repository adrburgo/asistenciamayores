import io
import logging
import subprocess
from pathlib import Path

import sounddevice as sd
import soundfile as sf

log = logging.getLogger("voice-service.tts")

PIPER_MODELS_DIR = Path("/app/models/piper")


class TTSEngine:
    def __init__(self, voice: str, output_device: str) -> None:
        self._voice = voice
        self._output_device = None if output_device == "default" else int(output_device)
        PIPER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self._model_path = self._ensure_model(voice)

    def _ensure_model(self, voice: str) -> Path:
        model_file = PIPER_MODELS_DIR / f"{voice}.onnx"
        config_file = PIPER_MODELS_DIR / f"{voice}.onnx.json"
        if model_file.exists() and config_file.exists():
            return model_file

        log.info("Descargando voz Piper '%s'...", voice)
        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
        lang = voice.split("-")[0].replace("_", "/")
        for filename in [f"{voice}.onnx", f"{voice}.onnx.json"]:
            url = f"{base_url}/{lang}/{voice}/{filename}"
            dest = PIPER_MODELS_DIR / filename
            subprocess.run(["curl", "-sL", url, "-o", str(dest)], check=True)

        log.info("Voz Piper lista.")
        return model_file

    def speak(self, text: str) -> None:
        try:
            result = subprocess.run(
                ["piper", "--model", str(self._model_path), "--output_raw"],
                input=text.encode(),
                capture_output=True,
                check=True,
            )
            audio_data, sample_rate = sf.read(io.BytesIO(result.stdout), dtype="float32")
            sd.play(audio_data, samplerate=sample_rate, device=self._output_device)
            sd.wait()
        except Exception as e:
            log.error("Error en TTS: %s", e)
