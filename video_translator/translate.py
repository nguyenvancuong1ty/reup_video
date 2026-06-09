from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import replace
from typing import Protocol

from .models import Segment


class Translator(Protocol):
    def translate(self, segments: list[Segment], source_lang: str, target_lang: str) -> list[Segment]:
        ...


class MockTranslator:
    def translate(self, segments: list[Segment], source_lang: str, target_lang: str) -> list[Segment]:
        translated: list[Segment] = []
        for seg in segments:
            translated.append(
                replace(
                    seg,
                    translated_text=f"[{source_lang}->{target_lang}] {seg.text}",
                )
            )
        return translated


class OpenRouterTranslator:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1",
        http_referer: str = "",
        app_title: str = "video-translator",
        timeout: int = 120,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.http_referer = http_referer
        self.app_title = app_title
        self.timeout = timeout

    def translate(self, segments: list[Segment], source_lang: str, target_lang: str) -> list[Segment]:
        if not self.api_key:
            raise ValueError("OpenRouter API key is missing. Set openrouter_api_key in config or OPENROUTER_API_KEY.")
        if not segments:
            return []

        payload = self._build_payload(segments, source_lang, target_lang)
        response = self._post_json(f"{self.base_url}/chat/completions", payload)
        content = response["choices"][0]["message"]["content"]
        parsed = self._parse_content(content)
        translated_by_id = {item["id"]: item["translated_text"] for item in parsed["segments"]}

        translated: list[Segment] = []
        for seg in segments:
            translated.append(
                replace(
                    seg,
                    translated_text=translated_by_id.get(seg.id, seg.text),
                )
            )
        return translated

    def _build_payload(self, segments: list[Segment], source_lang: str, target_lang: str) -> dict:
        schema = {
            "name": "translation_batch",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {"type": "integer"},
                                "translated_text": {"type": "string"},
                            },
                            "required": ["id", "translated_text"],
                        },
                    }
                },
                "required": ["segments"],
            },
            "strict": True,
        }
        segment_payload = [
            {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
            }
            for seg in segments
        ]
        system = (
            "You are a professional subtitle translator. "
            "Translate the provided subtitle segments from the source language to the target language. "
            "Keep the meaning natural, concise, and suitable for subtitles. "
            "Return only valid JSON that matches the schema."
        )
        user = {
            "source_lang": source_lang,
            "target_lang": target_lang,
            "segments": segment_payload,
            "instructions": [
                "Preserve segment ids.",
                "Make translated text concise enough for subtitles.",
                "Do not add commentary.",
                "Return only JSON.",
            ],
        }
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_schema", "json_schema": schema},
            "temperature": 0.2,
            "max_completion_tokens": 1200,
        }

    def _post_json(self, url: str, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            headers["X-Title"] = self.app_title

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter request failed: {exc.code} {exc.reason}\n{body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

    def _parse_content(self, content: str) -> dict:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenRouter response was not valid JSON: {content}") from exc

        if "segments" not in parsed or not isinstance(parsed["segments"], list):
            raise RuntimeError(f"OpenRouter response missing segments array: {parsed}")
        return parsed

