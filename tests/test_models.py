"""The schema has to reject ambiguous instructions before anything touches the screen."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from strands_xa11y.models import (
    ActAction,
    DesktopInput,
    ElementTarget,
    InspectInput,
    MouseAction,
    PointerTarget,
    ScreenshotAction,
    ScrollAction,
)


def test_element_target_requires_exactly_one_locator():
    ElementTarget(ref="e1")
    ElementTarget(selector="button")
    with pytest.raises(ValidationError, match="exactly one"):
        ElementTarget(app="TextEdit")
    with pytest.raises(ValidationError, match="exactly one"):
        ElementTarget(selector="button", ref="e1")


def test_pointer_target_admits_a_point_but_still_only_one():
    assert PointerTarget(point=(10, 20)).point == (10, 20)
    with pytest.raises(ValidationError, match="exactly one"):
        PointerTarget(point=(1, 2), selector="button")


@pytest.mark.parametrize(
    ("verb", "missing"),
    [("set_number", "number"), ("select_text", "start"), ("raw", "action_name")],
)
def test_act_verbs_declare_their_own_required_fields(verb, missing):
    with pytest.raises(ValidationError, match=missing):
        ActAction(type="act", target=ElementTarget(ref="e1"), verb=verb)


def test_act_verb_with_its_field_supplied_is_accepted():
    action = ActAction(type="act", target=ElementTarget(ref="e1"), verb="set_number", number=0.5)
    assert action.number == 0.5


def test_scroll_needs_a_direction():
    with pytest.raises(ValidationError, match="non-zero"):
        ScrollAction(type="scroll", target=PointerTarget(ref="e1"))


def test_screenshot_takes_a_target_or_a_region_not_both():
    with pytest.raises(ValidationError, match="not both"):
        ScreenshotAction(type="screenshot", target=ElementTarget(ref="e1"), region=(0, 0, 10, 10))


def test_mouse_move_needs_somewhere_to_move_to():
    with pytest.raises(ValidationError, match="requires a target"):
        MouseAction(type="mouse", op="move")
    MouseAction(type="mouse", op="down", button="left")


def test_discriminator_picks_the_right_action_model():
    parsed = DesktopInput.model_validate({"action": {"type": "click", "target": {"ref": "e7"}}})
    assert parsed.action.type == "click"
    assert parsed.action.target.ref == "e7"


def test_inspect_input_rejects_mutating_actions():
    """The read-only tool's schema is the enforcement point, not a runtime check."""
    with pytest.raises(ValidationError):
        InspectInput.model_validate({"action": {"type": "click", "target": {"ref": "e7"}}})
    assert InspectInput.model_validate({"action": {"type": "list_apps"}}).action.type == "list_apps"
