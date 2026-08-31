"""Verifier helpers that do not require a live LLM."""

from core.verifier import _format_evidence


def test_format_evidence_empty():
    text = _format_evidence([])
    assert "no tools" in text.lower()


def test_format_evidence_with_tools():
    trace = [
        {"name": "bash", "output": "hello world" * 200},
        {"name": "read_file", "output": "file content"},
    ]
    text = _format_evidence(trace)
    assert "bash" in text
    assert "read_file" in text
    assert len(text) < 5000
