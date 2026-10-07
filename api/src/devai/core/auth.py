"""Development API-key authentication shared by all protected routers."""

from secrets import compare_digest
from typing import Annotated

from fastapi import Header, HTTPException, Request


def require_api_key(request: Request, x_api_key: Annotated[str | None, Header()] = None):
    expected = request.app.state.settings.admin_api_key
    if x_api_key is None or not compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(401, "Unauthorized")
