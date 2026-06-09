from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import Segment
from .utils import run_cmd


class Extractor(Protocol):
    def extract(self, input_video: str) -> list[Segment]:
        ...


class WhisperLocalExtractor:
    def __init__(self, model_name: str = "small", device: str = "cpu", compute_type: str = "int8"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type

    def extract(self, input_video: str) -> list[Segment]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ImportError(
                "faster-whisper is not installed. Run `pip install -e .` or `pip install faster-whisper`."
            ) from exc

        model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
        segments_out: list[Segment] = []
        segments, _info = model.transcribe(input_video, vad_filter=True)

        for idx, seg in enumerate(segments, start=1):
            text = (seg.text or "").strip()
            if not text:
                continue
            segments_out.append(
                Segment(
                    id=idx,
                    start=float(seg.start),
                    end=float(seg.end),
                    text=text,
                )
            )

        return segments_out


class SubtitleTrackExporter:
    def export(self, input_video: str, out_srt: str) -> str:
        path = Path(out_srt)
        path.parent.mkdir(parents=True, exist_ok=True)
        run_cmd([
            "ffmpeg",
            "-y",
            "-i",
            input_video,
            "-map",
            "0:s:0?",
            out_srt,
        ])
        return str(path)

