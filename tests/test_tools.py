"""The Strands-facing surface: names, schemas, and what an agent actually sees."""

from __future__ import annotations

from strands_xa11y import inspect_desktop, use_desktop


def test_tools_register_under_their_own_names():
    assert use_desktop.tool_name == "use_desktop"
    assert inspect_desktop.tool_name == "inspect_desktop"


def test_descriptions_teach_the_workflow():
    description = use_desktop.tool_spec["description"]
    assert "accessibility tree" in description
    assert "snapshot" in description
    assert "refs" in description.lower()


def variants(tool) -> set:
    """The action models a tool's schema offers, by name."""
    return {name for name in tool.tool_spec["inputSchema"]["json"]["$defs"] if name.endswith("Action")}


def test_input_schema_exposes_every_action_as_a_variant():
    offered = variants(use_desktop)
    assert {"SnapshotAction", "ClickAction", "TypeAction", "ActAction", "KeyAction", "DragAction"} <= offered


def test_the_read_only_tool_offers_no_way_to_act():
    offered = variants(inspect_desktop)
    assert {"SnapshotAction", "FindAction", "ReadAction", "ScreenshotAction"} <= offered
    assert offered & {"ClickAction", "TypeAction", "DragAction", "OpenAppAction", "CloseAppAction"} == set()


def test_calling_the_tool_directly_runs_the_action(editor):
    result = use_desktop({"action": {"type": "list_apps"}})
    assert result["status"] == "success"
    assert "TextEdit" in result["content"][0]["text"]
