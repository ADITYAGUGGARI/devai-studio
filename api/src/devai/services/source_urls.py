"""Canonical URL identity for source deduplication; never fetches arbitrary URLs."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid", "igshid", "ref", "source"}


def canonical_source_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("An HTTPS source URL without embedded credentials is required")
    hostname = parts.hostname.lower().rstrip(".")
    port = parts.port
    authority = hostname if port in (None, 443) else f"{hostname}:{port}"
    path = parts.path.rstrip("/") or "/"
    params = sorted(
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in TRACKING_KEYS
    )
    return urlunsplit(("https", authority, path, urlencode(params), ""))
