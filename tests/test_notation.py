"""Range notation, and the one thing a 169-class spec cannot say.

``notation.parse`` is how a lesson describes a range, which makes it the widest surface in the engine: a
silent mis-parse does not raise, it just draws a different range in both languages and both prose
paragraphs. So the round-trip and the class-arithmetic below are the load-bearing tests, and the
``exclude`` case exists because a flop range that still contains board cards is not a slightly wrong
range -- it is a range describing hands that cannot be dealt. The last section guards the other boundary:
the committed 13x13 chart artifact is the only way a lesson's range reaches the engine, so the unit
conversion at that edge (cell frequency in, per-combo probability out) is tested against the real file.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pokergto.cards import Card, combos_for_class, parse_cards
from pokergto.errors import InputError, NotationError
from pokergto.notation import expand, parse, to_spec
from pokergto.ranges import Range, from_chart, to_chart_payload

KHEPT3D = ("Kh", "7s", "3d")


# --- class arithmetic ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("spec", "combos"),
    [
        ("AA", 6),
        ("AKs", 4),
        ("AKo", 12),
        ("22+", 78),
        ("AKs,AKo", 16),
        ("22+,ATs+", 114),
    ],
)
def test_specs_expand_to_their_combo_counts(spec: str, combos: int) -> None:
    assert parse(spec).total_combos() == pytest.approx(float(combos))


def test_fractional_classes_contribute_a_fraction_of_their_combos() -> None:
    """Half a suited class is two combos, not one and not four.

    The frequency is per combo, which is what lets a mixed strategy from a solver survive a round trip:
    the grid cell and the combo count have to agree about what ``0.5`` means.
    """
    assert parse("AKs:0.5").total_combos() == pytest.approx(2.0)
    assert parse("AKo:0.25").total_combos() == pytest.approx(3.0)


def test_a_run_and_a_set_are_not_the_same_thing() -> None:
    """``ATs+`` is the suited run *without* AKs/AQs/AJs, and both directions of a descending run parse."""
    ascending = parse("ATs+")
    explicit = parse("ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s")
    assert ascending.equal(explicit)
    assert parse("A9s-A2s").equal(parse("A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s"))


# --- round trip ------------------------------------------------------------------------


@pytest.mark.parametrize("spec", ["22+", "AKs", "KQo+", "22+,ATs+", "A5s-A2s", "88+,A9s+,KTs+"])
def test_parse_to_spec_round_trips_exactly(spec: str) -> None:
    rng = parse(spec)
    assert parse(to_spec(rng)).equal(rng)


def test_to_spec_refuses_to_lose_information_in_strict_mode() -> None:
    """A single physical combo cannot be named by 169-class notation.

    ``to_spec`` in strict mode raises instead of quietly emitting ``AKs`` for ``AsKs``, because a chart
    that says "this class" while meaning "this one suit" would make the artifact and the lesson disagree
    about which hands are being discussed.
    """
    single = Range.from_cards([Card.parse("As"), Card.parse("Ks")])
    with pytest.raises(NotationError):
        to_spec(single)
    assert to_spec(single, lossy=True)


def test_lowering_a_class_frequency_is_refused_rather_than_silently_ignored() -> None:
    """Asymmetric on purpose, and the asymmetry is the claim.

    Re-stating a class with a *higher* frequency is treated as an edit and wins; restating it with a
    lower one raises. Raising is the ordinary case of "actually I play AKs 75% of the time", while
    silently dropping a downgrade would let a spec that says ``AKs:0.75,AKs:0.25`` mean 0.75 and read
    like 0.25. A one-line test would have pinned the opposite behaviour and been wrong.
    """
    assert parse("AKs:0.25,AKs:0.75").frequency_map() == {"AKs": 0.75}
    with pytest.raises(NotationError):
        parse("AKs:0.75,AKs:0.25")


def test_empty_and_unknown_specs_are_refused() -> None:
    for bad in ("", "   ", "ZZ", "A7o-A2o,BadToken"):
        with pytest.raises(NotationError):
            parse(bad)


# --- board exclusion -------------------------------------------------------------------


def test_a_range_after_a_flop_cannot_contain_a_board_card() -> None:
    """The bug this parameter exists to make impossible.

    "77" is written identically preflop and on ``Kh7s3d``, but on that board only three of its six
    combos can be dealt. Before ``exclude`` the notation layer had no way to say so, and nut shares were
    computed against combos that do not exist -- hero's share read 0.1154 where the physical hands give
    0.0682, and no number disagreed loudly enough to be noticed.
    """
    board = parse_cards("Kh7s3d")
    naive = parse("77")
    honest = parse("77", exclude=board)
    assert naive.total_combos() == pytest.approx(6.0)
    assert honest.total_combos() == pytest.approx(3.0)
    # The removed combos are exactly the ones holding the seven of spades.
    held = {(first.code, second.code) for first, second, _ in honest}
    assert all("7s" not in combo for combo in held)
    assert len(held) == 3


def test_exclusion_removes_impossible_cards_from_every_class_not_just_pairs() -> None:
    """Every class shape loses a different number, and none of them is guessable.

    On ``Ah Ks Qh``: ``AKs`` drops from 4 to 2 (the heart and spade combos are gone), ``AQs`` from 4 to
    3 (only ``AhQh`` is dead -- it is a single combo that belongs to both blocked suits), ``KQs`` from 4
    to 2, ``AA`` from 6 to 3, and ``AKo`` from 12 to 7 rather than the 6 that "minus the Ah combos minus
    the Ks combos" suggests, because the combo carrying both is ``AsKs``, which is not an offsuit combo
    at all. Counting by class arithmetic is wrong even when the answer happens to look plausible, which
    is why the engine enumerates combos and these expectations are enumerated with it.
    """
    board = parse_cards("AhKsQh")
    assert parse("AKs", exclude=board).total_combos() == pytest.approx(2.0)
    assert parse("AQs", exclude=board).total_combos() == pytest.approx(3.0)
    assert parse("KQs", exclude=board).total_combos() == pytest.approx(2.0)
    assert parse("AA", exclude=board).total_combos() == pytest.approx(3.0)
    assert parse("AKo", exclude=board).total_combos() == pytest.approx(7.0)


def test_excluding_nothing_is_identical_to_the_plain_parse() -> None:
    """The preflop path must not change, or every preflop artifact would silently drift.

    ``exclude`` defaults to empty precisely so the safe, overwhelmingly common case is the one that
    needs no thought at the call site.
    """
    assert parse("22+,ATs+").equal(parse("22+,ATs+", exclude=()))


def test_expansion_reports_class_keys_without_removal() -> None:
    """``expand`` is the class-arithmetic a lesson quotes, so it stays the untouched 6/4/12.

    Mixing removal into it would make "how many combos does AKo have" answer "twelve, usually" -- the
    number a learner needs to be able to derive, and the one the removal lesson then subtracts from.
    """
    assert dict(expand("AKo"))["AKo"] == 12
    assert combos_for_class("AA") == 6
    assert combos_for_class("AKs") == 4


# --- the chart artifact boundary --------------------------------------------------------


CHART = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "gen"
    / "ranges"
    / "range.02-03.mdf-floor-vs-half-pot.json"
)


def test_chart_round_trip_keeps_per_combo_weights_probabilities() -> None:
    """``from_chart`` reads a cell as a frequency and ``Range`` stores one probability per combo.

    Those are the same number, which is exactly what makes the conversion easy to get wrong: multiplying
    a cell's frequency by its combo count -- the arithmetic ``combos()`` performs on the way *out* --
    yields a per-combo weight of up to twelve, which is not a probability, and ``Range`` refuses it. The
    committed chart is the fixture on purpose: lesson 01-04 and the chapter 03 lessons cite equities
    computed from a range built out of this file, and a range that cannot be constructed makes every one
    of those reproduce commands a fiction that no test notices.
    """
    artifact = json.loads(CHART.read_text(encoding="utf-8"))
    rng = from_chart(artifact)
    assert rng.weights.max() <= 1.0
    assert rng.total_combos() == pytest.approx(artifact["total_combos"])
    assert to_chart_payload(rng) == artifact["weights"]
    # Two thirds of the dealing space is the point of a half-pot MDF floor, in combos not cells.
    assert rng.total_combos() == pytest.approx(1326 * 2 / 3, abs=1e-3)
    assert rng.complement().total_combos() == pytest.approx(1326 / 3, abs=1e-3)
    assert rng.combos("84o") == pytest.approx(12 * 0.333333)


def test_a_chart_with_the_wrong_declared_combo_count_is_refused() -> None:
    """``cell_combos`` is checked against the deck, so a chart cannot quietly redefine what ``AKo`` means.

    This is the same guard ``from_chart`` has always had, stated as a test because the failure it prevents
    -- a hand-typed combo table -- is the failure mode ADR-0001 exists to remove.
    """
    artifact = json.loads(CHART.read_text(encoding="utf-8"))
    artifact["cell_combos"]["AKo"] = 4
    with pytest.raises(InputError, match="declares 4 combos for AKo"):
        from_chart(artifact)
