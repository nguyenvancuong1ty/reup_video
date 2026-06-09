from __future__ import annotations

from .extract import WhisperLocalExtractor
from .models import JobConfig
from .render import render_final_video
from .translate import MockTranslator, OpenRouterTranslator
from .tts import SilenceTTS, synthesize_segments
from .utils import ensure_dir, write_json


def _build_translator(config: JobConfig):
    if config.provider == "openrouter":
        return OpenRouterTranslator(
            api_key=config.openrouter_api_key,
            model=config.openrouter_model,
            base_url=config.openrouter_base_url,
            http_referer=config.openrouter_http_referer,
            app_title=config.openrouter_app_title,
        )
    return MockTranslator()


def run_job(config: JobConfig) -> dict[str, str]:
    workdir = ensure_dir(config.workdir)
    ensure_dir(workdir / "segments")
    ensure_dir(workdir / "voice")

    extractor = WhisperLocalExtractor(
        model_name=config.whisper_model,
        device=config.whisper_device,
        compute_type=config.whisper_compute_type,
    )
    segments = extractor.extract(config.input_video)
    write_json(workdir / "segments.json", [seg.to_dict() for seg in segments])

    translator = _build_translator(config)
    translated_segments = translator.translate(segments, config.source_lang, config.target_lang)
    write_json(workdir / "translated_segments.json", [seg.to_dict() for seg in translated_segments])

    tts = SilenceTTS()
    voiced_segments = synthesize_segments(translated_segments, tts, config.voice, str(workdir / "voice"))
    write_json(workdir / "voiced_segments.json", [seg.to_dict() for seg in voiced_segments])

    from .render import build_srt
    subtitle_source = str(workdir / "translated.srt")
    (workdir / "translated.srt").write_text(build_srt(voiced_segments), encoding="utf-8")

    output = render_final_video(config, voiced_segments, str(workdir), subtitle_source=subtitle_source)
    return {
        "output_video": output,
        "segments_json": str(workdir / "segments.json"),
        "translated_json": str(workdir / "translated_segments.json"),
        "voiced_json": str(workdir / "voiced_segments.json"),
    }
