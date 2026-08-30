"""Basic unit tests for tools (no LLM required)."""

from core.tools import tool_list_dir, tool_write_file, tool_read_file, tool_bash


def test_list_dir():
    r = tool_list_dir(".")
    assert r.success
    assert "main.py" in r.output or "config.py" in r.output


def test_write_and_read(tmp_path):
    p = tmp_path / "demo.txt"
    w = tool_write_file(str(p), "hello clean agent")
    assert w.success
    r = tool_read_file(str(p))
    assert r.success
    assert "hello clean agent" in r.output


def test_bash_echo():
    r = tool_bash("echo test123")
    assert r.success
    assert "test123" in r.output
