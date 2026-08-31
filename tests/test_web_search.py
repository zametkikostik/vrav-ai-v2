"""web_search tool — real network call (no mock). Graceful on timeout."""

from core.tools import tool_web_search, execute_tool


def test_web_search_returns_results_or_graceful_error():
    r = tool_web_search("OpenAI", max_results=3)
    assert r.output
    assert isinstance(r.success, bool)
    if r.success:
        assert "http" in r.output.lower() or "Search results" in r.output
    else:
        low = r.output.lower()
        assert "error" in low or "no results" in low or "timeout" in low


def test_web_search_via_execute_tool():
    r = execute_tool("web_search", {"query": "Python programming", "max_results": 2})
    assert r.output
    assert isinstance(r.success, bool)


def test_web_search_empty_query_still_safe():
    r = tool_web_search("", max_results=1)
    assert isinstance(r.success, bool)
    assert r.output is not None
