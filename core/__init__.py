"""Core agent components."""

from .tools import TOOLS_SPEC, TOOL_MAP, ToolResult

__all__ = ["run_agent", "TOOLS_SPEC", "TOOL_MAP", "ToolResult"]


def __getattr__(name: str):
    if name == "run_agent":
        from .loop import run_agent
        return run_agent
    raise AttributeError(name)
