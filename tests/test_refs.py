"""Refs are the tool's addressing scheme, so their edges matter more than most."""

from __future__ import annotations

import pytest

from strands_xa11y._errors import ToolError
from strands_xa11y._refs import Ref, RefStore, quote, segment


def test_quote_picks_a_quote_the_value_does_not_contain():
    assert quote("Save") == "'Save'"
    assert quote("Alice's file") == '"Alice\'s file"'


def test_quote_gives_up_when_a_value_contains_both_quotes():
    """xa11y defines no escape, so an unquotable name has to fall back to another strategy."""
    assert quote("""he said "it's fine\"""") is None


def test_segment_omits_position_when_the_step_is_unique():
    assert segment("button", "Save", 1, 1) == "button[name='Save']"
    assert segment("button", "Save", 2, 3) == "button[name='Save']:nth(2)"
    assert segment("group", None, 1, 1) == "group"


def test_segment_drops_an_unquotable_name_but_keeps_position():
    assert segment("button", """a"b'c""", 2, 2) == "button:nth(2)"


def test_refs_are_never_reused():
    store = RefStore()
    first = store.issue("pid:1", "button", name="Save")
    second = store.issue("pid:1", "button", name="Save")
    assert first.ref != second.ref
    assert store.get(first.ref).name == "Save"


def test_unknown_ref_says_how_to_recover():
    with pytest.raises(ToolError, match="fresh snapshot"):
        RefStore().get("e999")


def test_store_evicts_oldest_entries_past_capacity():
    store = RefStore(capacity=2)
    oldest = store.issue("pid:1", "button")
    store.issue("pid:1", "button")
    store.issue("pid:1", "button")
    assert len(store) == 2
    with pytest.raises(ToolError):
        store.get(oldest.ref)


def test_selector_preference_puts_stable_id_first():
    ref = Ref(ref="e1", app_key="pid:1", role="button", stable_id="btn-1", path="window > button")
    assert ref.selectors() == ["[stable_id='btn-1']", "window > button"]


def test_a_ref_with_neither_selector_has_none_to_offer():
    assert Ref(ref="e1", app_key="pid:1", role="button").selectors() == []
