from __future__ import annotations

from pathlib import Path

from .models import JobConfig, Segment
from .utils import ensure_dir, run_cmd


def build_srt(segments: list[Segment]) -> str:
    blocks: list[str] = []
    for seg in segments:
        blocks.append(
            "\n".join(
                [
                    str(seg.id),
                    f"{_seconds_to_srt(seg.start)} --> {_seconds_to_srt(seg.end)}",
                    seg.translated_text or seg.text,
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def render_final_video(
    config: JobConfig,
    segments: list[Segment],
    workdir: str,
    subtitle_source: str | None = None,
) -> str:
    work = Path(workdir)
    ensure_dir(work)
    subtitle_path = work / "translated.srt"
    subtitle_path.write_text(build_srt(segments), encoding="utf-8")

    if config.burn_subtitles:
        effective_subtitle = subtitle_source or str(subtitle_path)
        escaped = str(effective_subtitle).replace("\\", "\\\\")
        vf = f"subtitles={escaped}"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            config.input_video,
            "-vf",
            vf,
            "-c:a",
            "copy",
            config.output_video,
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            config.input_video,
            "-i",
            str(subtitle_path),
            "-c",
            "copy",
            "-c:s",
            "mov_text",
            config.output_video,
        ]

    run_cmd(cmd)
    return config.output_video


def _seconds_to_srt(value: float) -> str:
    total_ms = int(round(value * 1000))
    hours, rem = divmod(total_ms, 3600 * 1000)
    minutes, rem = divmod(rem, 60 * 1000)
    seconds, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

