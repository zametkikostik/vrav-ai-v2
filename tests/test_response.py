"""Structured response and confidence helpers."""

from core.response import (
    AgentAnswer,
    build_structured_answer,
    estimate_confidence,
    extract_sources_from_trace,
)


def test_agent_answer_json_roundtrip():
    a = AgentAnswer(
        answer="ok",
        sources=["https://example.com"],
        tools_used=["web_search"],
        confidence=0.8,
        verified=True,
    )
    data = a.model_dump()
    assert data["answer"] == "ok"
    assert a.to_json()
    text = a.to_text()
    assert "ok" in text
    assert "https://example.com" in text


def test_extract_sources_files_and_urls():
    trace = [
        {"name": "read_file", "args": {"path": "main.py"}, "output": "code", "success": True},
        {
            "name": "web_search",
            "args": {"query": "bg gpt"},
            "output": "Search results:\n- Title\n  https://example.org/page\n",
            "success": True,
        },
        {"name": "bash", "args": {"command": "echo 1"}, "output": "1", "success": True},
    ]
    sources = extract_sources_from_trace(trace)
    assert "file:main.py" in sources
    assert any(s.startswith("https://") for s in sources)
    assert "tool:bash" in sources


def test_estimate_confidence_no_tools():
    c = estimate_confidence([], verified=False)
    assert 0.0 <= c <= 0.5


def test_estimate_confidence_with_tools():
    trace = [{"success": True}, {"success": True}, {"success": False}]
    c = estimate_confidence(trace, verified=True)
    assert c >= 0.6


def test_build_structured_answer():
    ans = build_structured_answer(
        "result text",
        ["read_file", "bash"],
        [{"name": "read_file", "args": {"path": "a.py"}, "output": "x", "success": True}],
        verified=True,
    )
    assert ans.answer == "result text"
    assert "read_file" in ans.tools_used
    assert ans.verified is True
