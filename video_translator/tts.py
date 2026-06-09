from __future__ import annotations

import wave
from pathlib import Path
from typing import Protocol

from .models import Segment
from .utils import ensure_dir


class TTSProvider(Protocol):
    def synthesize(self, text: str, out_path: str, voice: str) -> str:
        ...


class SilenceTTS:
    def synthesize(self, text: str, out_path: str, voice: str) -> str:
        # Placeholder for the audio generation stage.
        # Emits a short silent WAV so the render pipeline can be exercised end-to-end.
        path = Path(out_path)
        ensure_dir(path.parent)

        sample_rate = 24000
        duration_sec = max(0.5, min(4.0, len(text) / 12.0))
        frames = int(sample_rate * duration_sec)

        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00\x00" * frames)

        return str(path)


def synthesize_segments(
    segments: list[Segment],
    tts: TTSProvider,
    voice: str,
    out_dir: str,
) -> list[Segment]:
    ensure_dir(out_dir)
    updated: list[Segment] = []
    for seg in segments:
        audio_path = str(Path(out_dir) / f"{seg.id:04d}.wav")
        tts.synthesize(seg.translated_text or seg.text, audio_path, voice)
        updated.append(
            Segment(
                id=seg.id,
                start=seg.start,
                end=seg.end,
                text=seg.text,
                translated_text=seg.translated_text,
                audio_path=audio_path,
            )
        )
    return updated

