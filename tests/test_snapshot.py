"""The snapshot is what the model reads every turn; its shape is a contract."""

from __future__ import annotations

import re

from strands_xa11y._actions import run
from strands_xa11y.models import SnapshotAction


def snapshot(**fields) -> str:
    result = run(SnapshotAction(type="snapshot", **fields))
    assert result["status"] == "success", result
    return result["content"][0]["text"]


def test_snapshot_renders_refs_names_values_and_states(editor):
    text = snapshot(app="TextEdit")
    assert "TextEdit (pid 4242)" in text
    assert re.search(r"e\d+ button \"Bold\"", text)
    assert re.search(r"e\d+ button \"Italic\" \[disabled\]", text)
    assert re.search(r"e\d+ text_field \"File name\" value=\"untitled\"", text)
    assert 'check_box "Wrap lines" [unchecked]' in text


def test_snapshot_indentation_tracks_tree_depth(editor):
    indents = {}
    for line in snapshot(app="TextEdit").splitlines():
        node = re.match(r"^(\s*)e\d+ (\w+)", line)
        if node:
            indents[node.group(2)] = len(node.group(1))
    assert indents["application"] == 0
    assert indents["window"] == 2
    assert indents["toolbar"] == 4
    assert indents["button"] == 6


def test_interactive_only_drops_decoration_but_keeps_containers(editor):
    text = snapshot(app="TextEdit")
    assert "separator" not in text
    assert " image" not in text
    # The unnamed group carries no meaning itself, but its children do.
    assert "group" in text


def test_everything_is_shown_when_the_filter_is_off(editor):
    text = snapshot(app="TextEdit", interactive_only=False)
    assert "separator" in text
    assert "image" in text


def test_truncation_is_reported_never_silent(editor):
    text = snapshot(app="TextEdit", max_nodes=3)
    assert "TRUNCATED" in text
    assert "max_nodes" in text


def test_depth_limit_stops_the_walk(editor):
    text = snapshot(app="TextEdit", max_depth=1)
    assert "window" in text
    assert "toolbar" not in text


def test_basic_detail_skips_state_reads(editor):
    """'basic' trades per-node state for a single bulk call — the Linux escape hatch."""
    text = snapshot(app="TextEdit", detail="basic")
    assert "button" in text
    assert "[disabled]" not in text


def test_bounds_are_opt_in(editor):
    assert "@10,20 300x400" not in snapshot(app="TextEdit")
    assert "@10,20 300x400" in snapshot(app="TextEdit", include_bounds=True)


def test_scoping_to_a_selector_narrows_the_tree(editor):
    text = snapshot(app="TextEdit", selector="toolbar")
    assert "button" in text
    assert "text_area" not in text
