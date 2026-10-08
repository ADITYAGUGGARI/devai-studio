"""Server-only JSON requests with bounded timeouts and safe provider errors."""

import os
import time

import httpx


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


def post_json(path: str, payload: dict, *, timeout: int = 180) -> dict:
    from devai.services.usage import record_usage

    started = time.monotonic()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ProviderError("OPENAI_API_KEY is not configured; set it on the server and restart")
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
