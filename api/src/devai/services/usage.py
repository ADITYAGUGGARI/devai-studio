"""Record provider usage without retaining prompts or credentials."""

import json
import logging
import os
import uuid
from contextlib import contextmanager
from contextvars import ContextVar

from devai.models import UsageEvent

_scope = ContextVar("provider_usage", default=None)


@contextmanager
def usage_scope(factory, job_id=None):
    token = _scope.set((factory, job_id))
    try:
        yield
    finally:
        _scope.reset(token)


def record_usage(operation: str, model: str, response: dict, duration_ms: int, status="completed"):
    scope = _scope.get()
    if not scope:
        return
    usage = response.get("usage") or {}
    inputs = usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0
    outputs = usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0
    images = len(response.get("data", [])) if operation == "images/generations" else 0
    # Rates are explicitly configured, never invented or presented as invoice totals.
    try:
        rates = json.loads(os.getenv("PROVIDER_PRICE_RATES_JSON", "{}")).get(model)
        cost = None
        if rates and all(k in rates for k in ["input_per_million", "output_per_million"]):
            cost = (
                inputs * rates["input_per_million"] / 1e6
                + outputs * rates["output_per_million"] / 1e6
            )
            if images:
                cost = cost + images * rates["per_image"] if "per_image" in rates else None
        factory, job_id = scope
        with factory.begin() as db:
            db.add(
                UsageEvent(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    model=model,
                    operation=operation,
                    status=status,
                    input_tokens=inputs,
                    output_tokens=outputs,
                    images=images,
                    estimated_cost_usd=cost,
                    pricing_json=json.dumps(rates) if rates else None,
                    duration_ms=duration_ms,
                )
            )
    except Exception:
        logging.getLogger(__name__).exception("Unable to persist provider usage")
