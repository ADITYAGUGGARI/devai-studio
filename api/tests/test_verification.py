"""Grounding must survive harmless formatting without accepting invented evidence."""

import json

import pytest

from devai.services import verification

SOURCE = "https://example.com/source"
CONTENT = {"caption": f"Engineering analysis. Source: {SOURCE}", "slides": []}


def audit(
    claim="Measured extraction accuracy",
    quote="The extractor scores 97.4 of 100.",
    supported=True,
    issues=None,
):
    return {
        "supported": supported,
        "claims": [{"claim": claim, "evidence_quote": quote}],
        "issues": issues or [],
    }


def provider(monkeypatch, reports):
    calls = []
    responses = iter(reports)

    def send(path, payload):
        assert path == "chat/completions"
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["strict"] is True
        assert "VERBATIM" in payload["messages"][0]["content"]
        calls.append(json.loads(payload["messages"][1]["content"]))
        return {"choices": [{"message": {"content": json.dumps(next(responses))}}]}

    monkeypatch.setattr(verification, "post_json", send)
    return calls


def test_verbatim_grounding_passes_and_records_checked_quotes(monkeypatch):
    calls = provider(monkeypatch, [audit()])
    result = verification.verify_copy("The extractor scores 97.4 of 100.", CONTENT, SOURCE)
    assert result["supported"]
    assert result["claims"][0]["evidence_matched"]
    assert result["audit_attempts"] == 1
    assert len(calls) == 1


def test_whitespace_and_quote_typography_do_not_cause_false_rejection(monkeypatch):
    provider(monkeypatch, [audit(quote="A “read-only” evaluator reports Hit@k and latency.")])
    result = verification.verify_copy(
        'A "read-only" evaluator reports\nHit@k\u00a0and latency.', CONTENT, SOURCE
    )
    assert result["supported"]


def test_reaudit_repairs_shortened_quote_without_changing_source_or_carousel(monkeypatch):
    calls = provider(monkeypatch, [audit(quote="The extractor... scores 97.4 of 100."), audit()])
    result = verification.verify_copy("The extractor scores 97.4 of 100.", CONTENT, SOURCE)
    assert result["supported"]
    assert result["audit_attempts"] == 2
    assert calls[0]["source_excerpt"] == calls[1]["source_excerpt"]
    assert calls[0]["carousel"] == calls[1]["carousel"]
    assert "correction" in calls[1]


@pytest.mark.parametrize(
    "quote",
    [
        "The extractor scores 99.4 of 100.",
        "The extractor scores...97.4 of 100.",
        "The extractor never scores 97.4 of 100.",
        "",
        " ",
        "the extractor scores 97.4 of 100.",
    ],
)
def test_changed_numbers_words_case_and_ellipsis_are_rejected_after_bounded_reaudit(
    monkeypatch, quote
):
    calls = provider(monkeypatch, [audit(quote=quote), audit(quote=quote)])
    result = verification.verify_copy("The extractor scores 97.4 of 100.", CONTENT, SOURCE)
    assert not result["supported"]
    assert len(calls) == 2
    assert not result["claims"][0]["evidence_matched"]
    assert len(result["issues"]) == 1
    assert "claims 1" in result["issues"][0]


def test_substantive_rejection_is_not_retried_or_overridden(monkeypatch):
    calls = provider(monkeypatch, [audit(supported=False, issues=["Invented benchmark"], quote="")])
    result = verification.verify_copy("The extractor scores 97.4 of 100.", CONTENT, SOURCE)
    assert not result["supported"]
    assert "Invented benchmark" in result["issues"]
    assert len(calls) == 1


def test_missing_citation_cannot_be_repaired_by_matching_quotes(monkeypatch):
    calls = provider(monkeypatch, [audit()])
    result = verification.verify_copy(
        "The extractor scores 97.4 of 100.", {"caption": "No source"}, SOURCE
    )
    assert not result["supported"]
    assert "citation" in result["issues"][0]
    assert len(calls) == 1


@pytest.mark.parametrize(
    "report",
    [
        {"supported": "true", "claims": [], "issues": []},
        {"supported": True, "claims": [None], "issues": []},
        {
            "supported": True,
            "claims": [{"claim": "", "evidence_quote": "Valid evidence"}],
            "issues": [],
        },
        {"supported": True, "claims": [], "issues": [123]},
        [],
    ],
)
def test_invalid_audit_report_fails_closed(monkeypatch, report):
    provider(monkeypatch, [report])
    with pytest.raises(ValueError, match="invalid report"):
        verification.verify_copy("Valid evidence", CONTENT, SOURCE)


def test_empty_audit_does_not_pass(monkeypatch):
    provider(monkeypatch, [{"supported": True, "claims": [], "issues": []}])
    result = verification.verify_copy("Source evidence", CONTENT, SOURCE)
    assert not result["supported"]
    assert result["issues"] == ["No source-grounded claims were recorded"]
