import pytest

from devai.services.generation import generate, validate_generated


def sample(url):
    return {
        "title": "A useful engineering update",
        "caption": "Practical analysis. Source: " + url,
        "slides": [
            {
                "headline": "Engineering insight",
                "body": "Evaluate this on representative production workloads.",
            }
            for _ in range(8)
        ],
    }


def test_valid_grounded_carousel():
    url = "https://example.com/story"
    assert len(validate_generated(sample(url), url)["slides"]) == 8


def test_source_required():
    with pytest.raises(ValueError, match="cite source"):
        validate_generated(sample("https://other.com"), "https://example.com")


def test_six_to_eight_slides_required():
    data = sample("https://example.com")
    data["slides"] = data["slides"][:5]
    with pytest.raises(ValueError, match="Six"):
        validate_generated(data, "https://example.com")


def test_missing_key_never_generates(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        generate("News", "https://example.com", "long excerpt " * 20)
