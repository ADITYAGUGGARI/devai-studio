"""Server-only JSON requests with bounded timeouts and safe provider errors."""

import os
import time
from contextlib import contextmanager
from contextvars import ContextVar

import httpx

_budget = ContextVar("provider_budget", default=None)


@contextmanager
def provider_budget(debit):
    token = _budget.set(debit)
    try:
        yield
    finally:
        _budget.reset(token)


def debit_budget():
    debit = _budget.get()
    if debit is not None:
        debit()


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


def speech_audio(script: str, *, voice: str = "coral") -> bytes:
    """Real speech response, never a silent audio substitute on provider failure."""
    from devai.services.usage import record_usage

    if voice not in {
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "onyx",
        "nova",
        "sage",
        "shimmer",
        "verse",
        "marin",
        "cedar",
    }:
        raise ValueError("Choose a supported narration voice")
    if not script.strip() or len(script) > 4096:
        raise ValueError("Narration must contain 1–4096 characters")
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ProviderError("OPENAI_API_KEY is not configured; set it on the server and restart")
    model = os.getenv("OPENAI_SPEECH_MODEL", "gpt-4o-mini-tts")
    debit_budget()
    started = time.monotonic()
    status = "failed"
    try:
        with httpx.stream(
            "POST",
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {key}"},
            timeout=180,
            json={
                "model": model,
                "input": script,
                "voice": voice,
                "instructions": "Clear, natural developer education narration. Do not add words.",
                "response_format": "wav",
            },
        ) as response:
            if response.is_error:
                raise ProviderError(
                    f"OpenAI speech HTTP {response.status_code}; check credentials, billing and model access",
                    retryable=response.status_code == 429 or response.status_code >= 500,
                )
            chunks, size = [], 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > 32 * 1024 * 1024:
                    raise ProviderError("Narration exceeded the supported audio size")
                chunks.append(chunk)
            raw = b"".join(chunks)
            if not raw.startswith(b"RIFF") or raw[8:12] != b"WAVE":
                raise ProviderError("Speech provider returned an invalid WAV response")
            status = "completed"
            return raw
    except httpx.RequestError as exc:
        raise ProviderError(
            "Narration request timed out or could not connect", retryable=True
        ) from exc
    finally:
        record_usage("audio/speech", model, {}, int((time.monotonic() - started) * 1000), status)


def post_json(path: str, payload: dict, *, timeout: int = 180) -> dict:
    from devai.services.usage import record_usage

    started = time.monotonic()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ProviderError("OPENAI_API_KEY is not configured; set it on the server and restart")
    debit_budget()
    try:
        response = httpx.post(
            f"https://api.openai.com/v1/{path}",
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=timeout,
        )
    except httpx.RequestError as exc:
        record_usage(
            path,
            payload.get("model", "unknown"),
            {},
            int((time.monotonic() - started) * 1000),
            "failed",
        )
        raise ProviderError(
            "OpenAI request timed out or could not connect", retryable=True
        ) from exc
    if response.is_error:
        record_usage(
            path,
            payload.get("model", "unknown"),
            {},
            int((time.monotonic() - started) * 1000),
            "failed",
        )
        code = response.status_code
        reason = ""
        try:
            reason = response.json().get("error", {}).get("code", "")
        except ValueError:
            pass
        quota = reason in {"insufficient_quota", "billing_hard_limit_reached"}
        raise ProviderError(
            f"OpenAI HTTP {code}. "
            + (
                "Check API billing and credits."
                if quota
                else "Check model access, credentials and provider limits."
            ),
            retryable=(code == 429 and not quota) or code >= 500,
        )
    result = response.json()
    record_usage(
        path, payload.get("model", "unknown"), result, int((time.monotonic() - started) * 1000)
    )
    return result
