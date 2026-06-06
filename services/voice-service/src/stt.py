import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

log = logging.getLogger("voice-service.stt")

SAMPLE_RATE = 16000
BLOCK_SIZE = 1600          # 100 ms a 16 kHz
AMPLITUDE_THRESHOLD = 0.02 # RMS mínimo para considerar que hay voz
SILENCE_TIMEOUT = 1.5      # segundos de silencio para cerrar la frase
MAX_PHRASE_SECONDS = 15    # corta si la frase es demasiado larga


class STTEngine:
    def __init__(self, model: str, language: str, input_device: str, wake_word: str, mqtt) -> None:  # noqa: ANN001
        self._language = language
        self._wake_word = wake_word.lower().strip()
        self._mqtt = mqtt
        self._paused = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        model_dir = Path("/app/models/whisper")
        model_dir.mkdir(parents=True, exist_ok=True)

        log.info("Cargando modelo Whisper '%s'...", model)
        self._model = WhisperModel(model, device="cpu", download_root=str(model_dir))
        log.info("Modelo Whisper listo.")

        self._device_index = None if input_device == "default" else int(input_device)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def _listen_loop(self) -> None:
        log.info("Escuchando audio (dispositivo: %s)...", self._device_index or "default")
        audio_buffer: list[np.ndarray] = []
        is_speaking = False
        silence_start: float | None = None
        phrase_start: float | None = None

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=BLOCK_SIZE,
            device=self._device_index,
        ) as stream:
            while not self._stop_event.is_set():
                if self._paused:
                    time.sleep(0.1)
                    continue

                block, _ = stream.read(BLOCK_SIZE)
                chunk = block.flatten()
                rms = float(np.sqrt(np.mean(chunk ** 2)))

                if rms > AMPLITUDE_THRESHOLD:
                    if not is_speaking:
                        log.debug("Voz detectada (RMS=%.4f).", rms)
                        is_speaking = True
                        phrase_start = time.monotonic()
                    audio_buffer.append(chunk)
                    silence_start = None
                elif is_speaking:
                    audio_buffer.append(chunk)
                    if silence_start is None:
                        silence_start = time.monotonic()

                    elapsed_silence = time.monotonic() - silence_start
                    elapsed_phrase = time.monotonic() - (phrase_start or 0)

                    if elapsed_silence >= SILENCE_TIMEOUT or elapsed_phrase >= MAX_PHRASE_SECONDS:
                        self._process_audio(np.concatenate(audio_buffer))
                        audio_buffer = []
                        is_speaking = False
                        silence_start = None
                        phrase_start = None

    def _process_audio(self, audio: np.ndarray) -> None:
        segments, info = self._model.transcribe(
            audio,
            language=self._language,
            beam_size=3,
            vad_filter=True,     # VAD integrado de faster-whisper (silero interno)
            vad_parameters={"min_silence_duration_ms": 500},
        )
        text = " ".join(s.text for s in segments).strip()
        if not text:
            return

        log.info("Transcripción: %s", text)

        if self._wake_word and self._wake_word not in text.lower():
            log.debug("Wake word no detectada, ignorando.")
            return

        text_clean = text
        if self._wake_word:
            text_clean = text.lower().replace(self._wake_word, "").strip().capitalize()

        self._mqtt.publish("asistente/texto", {
            "text": text_clean,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": info.language_probability,
        })
