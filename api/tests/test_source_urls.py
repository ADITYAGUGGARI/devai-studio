import pytest

from devai.services.source_urls import canonical_source_url


def test_tracking_parameters_and_fragment_removed():
    assert (
        canonical_source_url("https://EXAMPLE.com/story/?utm_source=email&b=2&a=1#comments")
        == "https://example.com/story?a=1&b=2"
    )


def test_different_query_content_is_preserved():
    assert canonical_source_url("https://example.com/search?q=ai") != canonical_source_url(
        "https://example.com/search?q=python"
    )


@pytest.mark.parametrize(
    "url",
    ["http://example.com", "https://user:pass@example.com", "file:///etc/passwd", "not a url"],
)
def test_reject_invalid_sources(url):
    with pytest.raises(ValueError):
        canonical_source_url(url)
