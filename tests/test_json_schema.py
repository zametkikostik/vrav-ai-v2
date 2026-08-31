"""JSON final-answer schema parse tests."""

from core.json_schema import parse_agent_json, merge_structured
from core.response import AgentAnswer


def test_parse_plain_json():
    text = '{"answer": "привет", "sources": ["tool:bash"], "confidence": 0.9}'
    a = parse_agent_json(text)
    assert a is not None
    assert a.answer == "привет"
    assert a.sources == ["tool:bash"]
    assert a.confidence == 0.9


def test_parse_fenced_json():
    text = """```json
{"answer": "ok", "sources": [], "confidence": 0.5}
```"""
    a = parse_agent_json(text)
    assert a is not None
    assert a.answer == "ok"


def test_parse_json_with_prefix_noise():
    text = 'Here is the result:\n{"answer": "done", "confidence": 0.7}\n'
    a = parse_agent_json(text)
    assert a is not None
    assert a.answer == "done"


def test_parse_not_json():
    assert parse_agent_json("просто текст без json") is None
    assert parse_agent_json("") is None
    assert parse_agent_json("{broken") is None


def test_merge_prefers_model_answer():
    parsed = AgentAnswer(answer="from model", sources=["https://a.test"], confidence=0.8)
    m = merge_structured(
        parsed, "fallback", ["web_search"], ["file:x"], verified=True, confidence=0.5
    )
    assert m.answer == "from model"
    assert "https://a.test" in m.sources
    assert "file:x" in m.sources


def test_merge_fallback_when_no_parse():
    m = merge_structured(
        None, "plain text", ["bash"], ["tool:bash"], verified=False, confidence=0.4
    )
    assert m.answer == "plain text"
    assert m.confidence == 0.4
