"""Real provider web search followed by bounded primary-source retrieval."""

import os
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import httpx

from devai.services.provider import post_json
from devai.services.research import (
    ARTICLE_HOSTS,
    ArticleText,
    _fetch_bounded,
    parse_published,
    source_error,
)

SEARCH_HOSTS = {
    "github.blog",
    "github.com",
    "openai.com",
    "anthropic.com",
    "developers.googleblog.com",
    "developers.google.com",
    "blog.google",
    "arxiv.org",
}
ARTICLE_HOSTS["Web Search"] = SEARCH_HOSTS


def search_web(query: str, *, now=None) -> dict:
    current = now or datetime.now(UTC)
    model = os.getenv("OPENAI_SEARCH_MODEL", "gpt-4.1-mini")
    tool = {"type": "web_search"}
    # Older search-capable models reject server-side domain filters. Retrieval
    # still enforces the same primary-source allowlist below.
    if not model.startswith(("gpt-4.1", "o4-mini")):
        tool["filters"] = {"allowed_domains": sorted(SEARCH_HOSTS)}
    response = post_json(
        "responses",
        {
            "model": model,
            "tools": [tool],
            "tool_choice": "required",
            "include": ["web_search_call.action.sources"],
            "input": f"Today is {current:%Y-%m-%d} UTC. Only consider publications between {current - timedelta(days=14):%Y-%m-%d} and {current:%Y-%m-%d}. Search recent primary-source developments relevant to software engineers: "
            + query
            + ". Cite canonical dated announcements or papers from the last 14 days, not generic landing pages. Do not invent URLs or dates.",
        },
    )
    links = {}
    for output in response.get("output", []):
        if output.get("type") == "web_search_call":
            for item in output.get("action", {}).get("sources", []):
                if item.get("url"):
                    links[item["url"]] = item.get("title", "")
        for content in output.get("content", []):
            for annotation in content.get("annotations", []):
                if annotation.get("type") == "url_citation":
                    links[annotation["url"]] = annotation.get("title", "")
    articles, errors = [], []
    for url, title in list(links.items())[:15]:
        if urlsplit(url).hostname not in SEARCH_HOSTS:
            continue
        try:
            with httpx.Client(
                timeout=12,
                follow_redirects=False,
                headers={"User-Agent": "DevAIStudio/1.0 (+source-attribution)"},
            ) as client:
                data, content_type = _fetch_bounded(client, url, 2_000_000, SEARCH_HOSTS)
            if "html" not in content_type.lower():
                continue
            page = ArticleText()
            page.feed(data.decode("utf-8", errors="replace"))
            dates = [
                parse_published(page.metadata[k])
                for k in [
                    "article:published_time",
                    "citation_date",
                    "citation_publication_date",
                    "date",
                    "dc.date",
                    "datepublished",
                ]
                if page.metadata.get(k)
            ]
            date = next((d for d in dates if d is not None), None)
            if not date or not timedelta(days=-1) <= current - date <= timedelta(days=14):
                errors.append(f"Web Search: no recent publisher date for {urlsplit(url).hostname}")
                continue
            excerpt = page.text()
            if len(excerpt) < 240:
                errors.append(
                    f"Web Search: insufficient readable evidence for {urlsplit(url).hostname}"
                )
                continue
            articles.append(
                {
                    "title": page.metadata.get("og:title")
                    or page.metadata.get("citation_title")
                    or title,
                    "url": url,
                    "source": "Web Search",
                    "published_at": date,
                    "summary": excerpt,
                }
            )
        except Exception as exc:
            errors.append(f"Web Search ({urlsplit(url).hostname}): {source_error(exc)}")
    return {"articles": articles, "errors": errors, "searched_urls": list(links)}
