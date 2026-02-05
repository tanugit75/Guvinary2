import base64
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import get_settings


class AudioPreprocessingError(Exception):
    pass


def decode_base64_audio(audio_base64: str) -> bytes:
    try:
        audio_bytes = base64.b64decode(audio_base64, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise AudioPreprocessingError("Invalid base64 payload") from exc

    settings = get_settings()
    if len(audio_bytes) > settings.max_audio_bytes:
        raise AudioPreprocessingError("Audio payload exceeds allowed size")

    return audio_bytes


def mp3_to_wav_16k_mono(mp3_bytes: bytes) -> tuple[np.ndarray, int]:
    settings = get_settings()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mp3_path = tmp_path / "input.mp3"
        wav_path = tmp_path / "output.wav"

        mp3_path.write_bytes(mp3_bytes)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(mp3_path),
            "-ac",
            "1",
            "-ar",
            str(settings.target_sample_rate),
            str(wav_path),
        ]

        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            raise AudioPreprocessingError(f"Failed to decode/convert audio: {process.stderr.strip()}")

        waveform, sample_rate = sf.read(wav_path, dtype="float32")

    if waveform.ndim > 1:
        waveform = waveform.mean(axis=1)

    if waveform.size == 0:
        raise AudioPreprocessingError("Audio is empty after preprocessing")

    return waveform, sample_rate
