"""Discover source-backed developer stories without treating feeds as verified copy."""

import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit

import httpx

FEEDS = {
    "GitHub Blog": "https://github.blog/feed/",
    "Google Developers": "https://developers.googleblog.com/feeds/posts/default",
    "OpenAI News": "https://openai.com/news/rss.xml",
    "Anthropic Claude Code": "https://raw.githubusercontent.com/anthropics/claude-code/main/feed.xml",
    "OpenAI Codex": "https://github.com/openai/codex/releases.atom",
    "Model Context Protocol": "https://github.com/modelcontextprotocol/modelcontextprotocol/releases.atom",
    "arXiv: Software Engineering": "https://export.arxiv.org/rss/cs.SE",
    "arXiv: Artificial Intelligence": "https://export.arxiv.org/rss/cs.AI",
}

# Source-page retrieval is limited to the official publishers already used for RSS.
ARTICLE_HOSTS = {
    "GitHub Blog": {"github.blog"},
    "Google Developers": {"developers.googleblog.com", "developers.google.com"},
    "OpenAI News": {"openai.com"},
    "Anthropic Claude Code": {"github.com"},
    "OpenAI Codex": {"github.com"},
    "Model Context Protocol": {"github.com"},
    "arXiv: Software Engineering": {"arxiv.org"},
    "arXiv: Artificial Intelligence": {"arxiv.org"},
}
RELEVANT_TITLE = re.compile(
    r"\b(ai|agent|llm|gpt(?:-\d)?|claude|gemini|mistral|gemma|llama|model|copilot|code|coding|developer|software|machine learning|security|python|api|retrieval|rag|evaluation|benchmark|mcp)\b",
    re.I,
)


class ArticleText(HTMLParser):
    """Extract readable article copy while skipping executable and page-chrome text."""

    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside", "form"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts = []
        self.metadata = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in self.SKIP:
            self._skip_depth += 1
        if tag == "meta":
            key = (attributes.get("property") or attributes.get("name") or "").lower()
            if key in {"og:title", "og:description", "description", "article:published_time"}:
                self.metadata[key] = attributes.get("content", "")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in {"p", "h1", "h2", "h3", "li", "blockquote", "br"} and not self._skip_depth:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)

    def text(self, limit=6000):
        return re.sub(r"\n{3,}", "\n\n", " ".join(self.parts)).strip()[:limit]


def parse_published(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def fetch_feed(url, timeout=8):
    """Fetch one capped RSS/Atom document; requests never follow redirects."""
    with httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        headers={"User-Agent": "DevAIStudio/1.0 (+source-attribution)"},
    ) as client:
        data, content_type = _fetch_bounded(client, url, max_bytes=1_000_000)
        content_type = content_type.lower()
        if not any(kind in content_type for kind in ("xml", "rss", "atom", "text/plain")):
            raise ValueError("Feed did not return an XML or plain-text document")
    root = ET.fromstring(data)
    items = []
    for item in root.findall(".//item")[:30]:
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        if title.strip() and link.startswith("https://"):
            items.append(
                {
                    "title": title.strip(),
                    "url": link.strip(),
                    "published": item.findtext("pubDate") or "",
                    "summary": item.findtext("description") or "",
                }
            )
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("a:entry", ns)[:30]:
        title = entry.findtext("a:title", default="", namespaces=ns)
        link = next(
            (
                element.attrib.get("href", "")
                for element in entry.findall("a:link", ns)
                if element.attrib.get("rel", "alternate") == "alternate"
            ),
            "",
        )
        published = entry.findtext("a:published", default="", namespaces=ns)
        updated = entry.findtext("a:updated", default="", namespaces=ns)
        content_element = entry.find("a:content", ns)
        content = (
            ET.tostring(content_element, encoding="unicode") if content_element is not None else ""
        )
        summary = entry.findtext("a:summary", default="", namespaces=ns)
        if title.strip() and link.startswith("https://"):
            items.append(
                {
                    "title": title.strip(),
                    "url": link.strip(),
                    "published": published or updated,
                    "summary": content or summary,
                }
            )
    return items


def clean_excerpt(value, limit=6000):
    parser = ArticleText()
    parser.feed(value or "")
    parser.close()
    return parser.text(limit)


def fetch_article(article, timeout=8):
    """Fetch only canonical HTTPS pages on this feed's publisher allowlist.

    Redirects are deliberately disabled so a trusted publisher cannot bounce the
    worker to a private IP address or an unrelated host.
    """
    allowed_hosts = ARTICLE_HOSTS.get(article.get("source"), set())
    parts = urlsplit(article.get("url", ""))
    if parts.scheme != "https" or parts.hostname not in allowed_hosts or parts.username:
        return ""
    with httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        headers={"User-Agent": "DevAIStudio/1.0 (+source-attribution)"},
    ) as client:
        with client.stream("GET", article["url"]) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type:
                return ""
            page = b"".join(_bounded_chunks(response, 2_000_000)).decode(
                response.encoding or "utf-8", errors="replace"
            )
    parser = ArticleText()
    parser.feed(page)
    parser.close()
    return parser.text()


def _bounded_chunks(response, max_bytes):
    consumed = 0
    for chunk in response.iter_bytes(chunk_size=32_768):
        remaining = max_bytes - consumed
        if remaining <= 0:
            break
        piece = chunk[:remaining]
        consumed += len(piece)
        if piece:
            yield piece
        if len(chunk) > remaining:
            break


def _fetch_bounded(client, url, max_bytes):
    with client.stream("GET", url) as response:
        response.raise_for_status()
        data = b"".join(_bounded_chunks(response, max_bytes))
        return data, response.headers.get("content-type", "")


def classify_topic(title, excerpt):
    text = f"{title} {excerpt[:1500]}".lower()
    if re.search(r"\b(api|sdk|tool|editor|copilot|plugin|ide|release|launch|introducing)\b", text):
        return "tools"
    if re.search(r"\b(tutorial|how to|guide|cookbook|walkthrough|example|quickstart)\b", text):
        return "tutorial"
    if re.search(
        r"\b(architecture|system design|infrastructure|production|scaling|serving|latency)\b", text
    ):
        return "architecture"
    if re.search(r"\b(research|paper|benchmark|evaluation|study|measurement)\b", text):
        return "insight"
    return "news"


def discover(feeds=None, *, now=None, max_age=timedelta(days=14)):
    """Return relevant, recent articles with a trustworthy timestamp and excerpt."""
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    articles, errors = [], []
    for name, feed_url in (FEEDS if feeds is None else feeds).items():
        try:
            for item in fetch_feed(feed_url):
                item["source"] = name
                if name in {"Anthropic Claude Code", "OpenAI Codex", "Model Context Protocol"}:
                    item["title"] = f"{name}: {item['title']}"
                item["published_at"] = parse_published(item.pop("published", ""))
                item["summary"] = clean_excerpt(item.get("summary", ""))
                date = item["published_at"]
                if not date or date > current.astimezone(UTC) + timedelta(days=1):
                    continue
                if current.astimezone(UTC) - date > max_age:
                    continue
                if RELEVANT_TITLE.search(item["title"]):
                    articles.append(item)
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}")
    articles.sort(key=lambda article: article["published_at"], reverse=True)
    return {"articles": articles[:50], "errors": errors}


def create_editorial_draft(article):
    """Create a visibly unverified scaffold for candidates without extracted evidence."""
    title = article["title"][:160]
    slides = [
        {
            "headline": title,
            "body": "A developer-focused story to investigate. Source linked in caption.",
        },
        {
            "headline": "WHAT WAS ANNOUNCED?",
            "body": "Check the primary source and verify the publisher's exact claim before approval.",
        },
        {
            "headline": "WHY DEVELOPERS CARE",
            "body": "Assess workflow, reliability, and maintainability.",
        },
        {
            "headline": "HOW DOES IT WORK?",
            "body": "Add a verified technical example or original diagram.",
        },
        {
            "headline": "PRODUCTION CHECKLIST",
            "body": "Assess latency, cost, security, observability, and fallback behavior.",
        },
        {
            "headline": "WHAT TO TEST",
            "body": "Benchmark against your own representative workloads.",
        },
        {
            "headline": "TRADE-OFFS",
            "body": "Identify limitations, prerequisites, and unsupported cases.",
        },
        {
            "headline": "YOUR TAKEAWAY",
            "body": "Write a useful conclusion after checking the source.",
        },
    ]
    return {
        "title": title,
        "caption": f"Developer news to verify: {title}\n\nPrimary source: {article['url']}\n\n#AIEngineering #SoftwareDevelopment",
        "slides": slides,
    }
