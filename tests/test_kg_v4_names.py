"""Names: equal canonical forms merge, differences of kind never do."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.kg_v4.names import (
    about_the_manual,
    adds_to_name,
    canonical,
    code_key,
    compound_action,
    contrast,
    display_name,
    distinguishing_difference,
    lemma,
    name_defects,
    similarity,
)

PAIRS = json.loads((Path(__file__).parent / "fixtures" / "kg_v4_entity_pairs.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("left, right", [
    ("drive roll", "Drive rolls"), ("3 phase", "three-phase"), ("The V-belt", "V-belts"), ("Lenses", "lens"),
    ("Fuses", "fuse"), ("Batteries", "battery"), ("Switches", "the switch"), ("AIR  VALVE.", "air valve"),
])
def test_names_that_are_the_same_name(left, right):
    assert canonical(left) == canonical(right)
    assert distinguishing_difference(left, right) == ""


@pytest.mark.parametrize("left, right, reason", [
    ("x axis limit switch", "y axis limit switch", "different axis or letter"),
    ("increase nozzle size", "decrease nozzle size", "opposite or alternative terms"),
    ("door open", "door closed", "opposite or alternative terms"),
    ("inner shaft sealing ring", "outer shaft sealing ring", "opposite or alternative terms"),
    ("Mirror #1", "Mirror #2", "different numbers"),
    ("brake clamped icon", "brake unclamped icon", "negated term"),
    ("Fan does not operate", "Fan operates normally", "negation"),
    ("Check the switch for open or short circuit with the door closed",
     "Check the switch for open or short circuit with the door open", "opposite or alternative terms"),
])
def test_false_friends_differ_in_kind(left, right, reason):
    assert canonical(left) != canonical(right)
    assert distinguishing_difference(left, right) == reason


def test_real_false_friends_are_caught_or_flagged_for_a_close_look():
    for item in PAIRS["false_friends"]:
        left, right = item["names"]
        assert canonical(left) != canonical(right), item
        # A hard difference, a contrast for the resolver, or names too far apart to be proposed.
        assert distinguishing_difference(left, right) or contrast(left, right) or similarity(left, right) < 0.78, item


def test_real_duplicates_are_never_blocked():
    for item in PAIRS["duplicates"]:
        left, right = item["names"]
        assert distinguishing_difference(left, right) == "", item


def test_the_same_words_in_another_order_are_only_a_contrast():
    assert canonical("air in water line") != canonical("water in air line")
    assert distinguishing_difference("air in water line", "water in air line") == ""
    assert contrast("air in water line", "water in air line") == "same words in a different order"
    assert contrast("tool probe", "work probe") == "one word differs: tool / work"


def test_lemma_is_small_and_predictable():
    assert [lemma(word) for word in ("bearings", "glass", "axis", "series", "gases", "hoses", "brushes")] == [
        "bearing", "glass", "axis", "series", "gas", "hose", "brush"]


def test_codes_compare_without_case_and_punctuation_but_keep_zeros():
    assert code_key("E-12") == code_key("e12") == "e12"
    assert code_key("007") != code_key("7")


def test_name_defects():
    assert name_defects("Unspecified cause of noise") == ["generic"]
    assert name_defects("Replace the") == ["truncated"]
    assert "layout_noise" in name_defects("Check valve ... page 12")
    assert name_defects("Drive belt") == []


def test_text_checks_for_descriptions_instructions_and_names():
    assert about_the_manual("This belt condition is listed as a possible cause of vibration.")
    assert about_the_manual("The manual identifies the tube as supported by two saddles.")
    assert not about_the_manual("Two soft-mount saddles and straps hold the CO2 laser tube.")
    assert not adds_to_name("Align the laser beam", "Align laser beam (Page 57).")
    assert not adds_to_name("Inspect the belts", "Inspect the belts")
    assert adds_to_name("Increase air pressure", "Shut off air at the gun, then increase air pressure to maximum.")
    assert compound_action("Adjust/replace belts") and not compound_action("Clean the inlet/outlet screens")
    assert display_name("water pump") == "Water pump" and display_name("pH sensor") == "pH sensor"
    assert display_name("x-axis belt") == "X-axis belt" and display_name("Table") == "Table"
