import json
import logging
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger("voice-service.tts")

PIPER_MODELS_DIR = Path("/app/models/piper")


class TTSEngine:
    def __init__(self, voice: str, output_device: str) -> None:
        self._voice = voice
        # ALSA device string (e.g. "plughw:1,31") or "default"
        self._alsa_device = output_device if output_device != "default" else "default"
        PIPER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self._model_path = self._ensure_model(voice)

    def _ensure_model(self, voice: str) -> Path:
        model_file = PIPER_MODELS_DIR / f"{voice}.onnx"
        config_file = PIPER_MODELS_DIR / f"{voice}.onnx.json"
        if model_file.exists() and config_file.exists():
            try:
                json.loads(config_file.read_text())
            except json.JSONDecodeError:
                config_file.unlink(missing_ok=True)
                model_file.unlink(missing_ok=True)
            else:
                return model_file

        log.info("Descargando voz Piper '%s'...", voice)
        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
        lang = voice.split("-")[0].replace("_", "/")
        for filename in [f"{voice}.onnx", f"{voice}.onnx.json"]:
            url = f"{base_url}/{lang}/{voice}/{filename}"
            dest = PIPER_MODELS_DIR / filename
            subprocess.run(["curl", "-fsSL", url, "-o", str(dest)], check=True)

        log.info("Voz Piper lista.")
        return model_file

    def speak(self, text: str) -> None:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            subprocess.run(
                ["piper", "--model", str(self._model_path), "--output_file", str(tmp_path)],
                input=text.encode(),
                capture_output=True,
                check=True,
            )

            # ffmpeg handles sample rate conversion (piper → 22050Hz, hardware needs 48000Hz)
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(tmp_path),
                    "-ar", "48000",
                    "-ac", "2",
                    "-f", "alsa",
                    self._alsa_device,
                ],
                capture_output=True,
                check=True,
            )
            log.debug("TTS reproducido correctamente.")
        except Exception as e:
            log.error("Error en TTS: %s", e)
        finally:
            if tmp_path:
                tmp_path.unlink(missing_ok=True)
