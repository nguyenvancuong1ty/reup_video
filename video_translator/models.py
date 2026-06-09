from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class Segment:
    id: int
    start: float
    end: float
    text: str
    translated_text: str = ""
    audio_path: str = ""

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JobConfig:
    input_video: str
    output_video: str
    source_lang: str = "ja"
    target_lang: str = "vi"
    subtitle_path: str | None = None
    burn_subtitles: bool = True
    keep_audio_bed: bool = True
    voice: str = "vi-VN-HoaiMyNeural"
    workdir: str = "work"
    provider: str = "mock"
    asr_provider: str = "whisper-local"
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str = ""
    openrouter_app_title: str = "video-translator"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "JobConfig":
        return JobConfig(
            input_video=data["input_video"],
            output_video=data["output_video"],
            source_lang=data.get("source_lang", "ja"),
            target_lang=data.get("target_lang", "vi"),
            subtitle_path=data.get("subtitle_path"),
            burn_subtitles=bool(data.get("burn_subtitles", True)),
            keep_audio_bed=bool(data.get("keep_audio_bed", True)),
            voice=data.get("voice", "vi-VN-HoaiMyNeural"),
            workdir=data.get("workdir", "work"),
            provider=data.get("provider", "mock"),
            asr_provider=data.get("asr_provider", "whisper-local"),
            whisper_model=data.get("whisper_model", "small"),
            whisper_device=data.get("whisper_device", "cpu"),
            whisper_compute_type=data.get("whisper_compute_type", "int8"),
            openrouter_api_key=data.get("openrouter_api_key", ""),
            openrouter_model=data.get("openrouter_model", "openai/gpt-4o-mini"),
            openrouter_base_url=data.get("openrouter_base_url", "https://openrouter.ai/api/v1"),
            openrouter_http_referer=data.get("openrouter_http_referer", ""),
            openrouter_app_title=data.get("openrouter_app_title", "video-translator"),
        )
