"""Failures are the tool's main teaching signal, so they get their own tests."""

from __future__ import annotations

import fake_xa11y
import pytest

from strands_xa11y._actions import run
from strands_xa11y._errors import describe
from strands_xa11y._session import require_consent
from strands_xa11y.models import ClickAction, ElementTarget, FindAction, PointerTarget, ScreenshotAction


def text_of(result) -> str:
    return result["content"][0]["text"]


def test_diagnosis_is_passed_through_verbatim():
    """xa11y's structured diagnosis is what lets the model fix its own selector."""
    message = describe(
        fake_xa11y.TimeoutError(
            "timed out",
            elapsed=5.0,
            condition="visible",
            selector="button[name='Sav']",
            last_observed="selector never matched",
            candidates=["button 'Save'", "button 'Save As…'"],
            scope="window 'Untitled'",
        )
    )
    assert "condition: visible" in message
    assert "selector: button[name='Sav']" in message
    assert "near misses: button 'Save'; button 'Save As…'" in message
    assert "search scope:" in message


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (fake_xa11y.PermissionDeniedError("nope"), "Privacy & Security"),
        (fake_xa11y.AccessibilityNotEnabledError("empty"), "--force-renderer-accessibility"),
        (fake_xa11y.ActionNotSupportedError("no"), "'actions' list"),
        (fake_xa11y.InvalidSelectorError("bad"), "snake_case"),
    ],
)
def test_each_failure_mode_carries_its_fix(error, expected):
    assert expected in describe(error)


def test_run_converts_backend_errors_into_tool_results(editor):
    result = run(FindAction(type="find", app="TextEdit", selector="button[name=unquoted]"))
    assert result["status"] == "error"
    assert "InvalidSelectorError" in text_of(result)


def test_mutating_actions_need_consent(editor, monkeypatch):
    monkeypatch.setenv("BYPASS_TOOL_CONSENT", "false")
    monkeypatch.setattr("builtins.input", lambda _: "n")
    monkeypatch.setattr("strands_xa11y._session.sys.stdin", type("Stdin", (), {"isatty": lambda self: True})())

    result = run(ClickAction(type="click", target=PointerTarget(app="TextEdit", selector="button[name='Bold']")))
    assert result["status"] == "error"
    assert "declined" in text_of(result)


def test_reading_the_tree_never_asks_for_consent(editor, monkeypatch):
    monkeypatch.setenv("BYPASS_TOOL_CONSENT", "false")
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("read-only actions must not prompt"))

    assert run(FindAction(type="find", app="TextEdit", selector="button"))["status"] == "success"


def test_sending_pixels_to_the_model_does_ask(editor, monkeypatch):
    """Withholding the image is free; shipping it is a privacy decision."""
    monkeypatch.setenv("BYPASS_TOOL_CONSENT", "false")
    monkeypatch.setattr("builtins.input", lambda _: "n")
    monkeypatch.setattr("strands_xa11y._session.sys.stdin", type("Stdin", (), {"isatty": lambda self: True})())

    assert run(ScreenshotAction(type="screenshot"))["status"] == "success"
    assert run(ScreenshotAction(type="screenshot", send_image=True))["status"] == "error"


def test_without_a_terminal_consent_is_refused_not_assumed(monkeypatch):
    monkeypatch.setenv("BYPASS_TOOL_CONSENT", "false")
    monkeypatch.setattr("strands_xa11y._session.sys.stdin", type("Stdin", (), {"isatty": lambda self: False})())

    with pytest.raises(Exception, match="BYPASS_TOOL_CONSENT"):
        require_consent("click(...)")


def test_consent_summary_names_the_target(editor, monkeypatch):
    monkeypatch.setenv("BYPASS_TOOL_CONSENT", "false")
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "y")
    monkeypatch.setattr("strands_xa11y._session.sys.stdin", type("Stdin", (), {"isatty": lambda self: True})())

    run(ClickAction(type="click", target=PointerTarget(app="TextEdit", selector="button[name='Bold']")))
    assert "click(" in prompts[0]
    assert "Bold" in prompts[0]


def test_missing_element_target_is_a_schema_error_not_a_crash():
    with pytest.raises(Exception, match="exactly one"):
        ElementTarget()
