"""Range notation: ``"22+,ATs+,KJo+,75s"`` <-> :class:`pokergto.ranges.Range`.

Conventions are pinned here and tested, because tools disagree and a silently-different ``+`` is
the kind of bug that makes two lessons state different ranges for the same spot.

* ``XY+`` where ``X > Y``: every ``XZ`` of the same suitedness with ``Z <= Y``. So ``ATs+`` is
  ``ATs, A9s, A8s, ..., A2s`` (it excludes ``AKs``), and ``AKs+`` is all suited aces.
* ``NN+`` for a pair: every pair with rank ``>= N``, so ``22+`` is all thirteen pairs.
* ``HI-LO``: the inclusive run between two partners of the same high card, e.g. ``A2s-A5s``;
  for pairs the direction is high-then-low, ``AA-77``.
* ``KEY:0.5``: a fractional frequency on a single class. Supported so that round-tripping a solver
  strategy (which is full of mixed frequencies) is lossless.
* ``;`` starts a comment line and ``[anything]`` is a section header, both ignored, so the common
  text range-file layout parses without a bespoke importer.

What notation cannot express: a specific *physical* subset of a class, such as "A of spades with K
of hearts only". ``to_spec`` raises in strict mode and sets ``lossy`` when it collapses one.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final

from .cards import GRID_RANKS, Card, combos_for_class
from .errors import NotationError
from .ranges import Range

_RANKS: Final[str] = "AKQJT98765432"
_RANK_INDEX: Final[dict[str, int]] = {r: i for i, r in enumerate(_RANKS)}  # 0 = ace, 12 = deuce
_TOKEN_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<high>[AKQJT98765432])(?P<low>[AKQJT98765432])(?P<shape>os|so|s|o)?"
    r"(?::(?P<freq>0?\.\d+|1\.0|1|0))?$"
)


def _shape_suffix(shape: str | None) -> str | None:
    if shape is None:
        return None
    if shape in ("os", "o"):
        return "o"
    if shape in ("s", "sf"):
        return "s"
    raise NotationError(f"unknown suitedness marker {shape!r}")


def _parse_atom(text: str) -> tuple[str, str, str | None, float]:
    """One atomic spec such as ``ATs``, ``AK``, ``AA``, ``AKs:0.5`` -> (high, low, shape, freq)."""
    match = _TOKEN_RE.match(text.strip())
    if match is None:
        raise NotationError(f"cannot parse range token {text!r}")
    return (
        match.group("high"),
        match.group("low"),
        _shape_suffix(match.group("shape")),
        float(match.group("freq")) if match.group("freq") is not None else 1.0,
    )


def _partners_below(high: str) -> list[str]:
    """Ranks that can be the second card of ``high``, in descending order. A pair has no partners."""
    start = _RANK_INDEX[high] + 1
    return list(_RANKS[start:])


def _run_target_rank(text: str) -> str:
    """The partner rank a run endpoint names. ``"AKs"``->K, ``"9s"``->9, ``"77"``->7, ``"A7"``->7.

    Different tools write run endpoints with or without the high card repeated and with or without
    a shape marker, so the rank is whatever rank character comes last. Ambiguity here would be a
    silent range change, which is the one thing a notation must never be.
    """
    ranks = [ch for ch in text if ch in _RANKS]
    if not ranks:
        raise NotationError(f"run endpoint {text!r} names no rank")
    return ranks[-1]


def _expand(token: str) -> list[tuple[str, float]]:
    raw = token.strip()
    if not raw:
        return []

    plus = raw.endswith("+")
    body = raw[:-1] if plus else raw
    run_target: str | None = None
    if not plus and "-" in body:
        body, run_target = body.split("-", 1)
        run_target = run_target.strip()

    high, low, shape, frequency = _parse_atom(body)

    # --- pocket pairs ---
    if high == low:
        if shape is not None:
            raise NotationError(f"{token!r}: a pocket pair has no suitedness marker")
        start = _RANK_INDEX[high]
        if plus:
            ranks = list(_RANKS[: start + 1])  # "TT+" = every pair at or above tens
        elif run_target is not None:
            end = _RANK_INDEX[_run_target_rank(run_target)]
            lo, hi = sorted((start, end))
            ranks = list(_RANKS[lo : hi + 1])
        else:
            ranks = [high]
        return [(f"{r}{r}", frequency) for r in ranks]

    # --- non-pairs ---
    if high == "2":
        raise NotationError(f"{token!r}: deuce cannot be the high card")
    suffix = shape or "s"
    candidates = [f"{high}{p}{suffix}" for p in _partners_below(high)]
    anchor = f"{high}{low}{suffix}"
    if anchor not in candidates:
        raise NotationError(f"{token!r}: {low} is not a partner of {high}")
    position = candidates.index(anchor)

    if run_target is not None:
        end_key = f"{high}{_run_target_rank(run_target)}{suffix}"
        if end_key not in candidates:
            raise NotationError(
                f"{token!r}: cannot run from {low} to {_run_target_rank(run_target)}"
            )
        end_position = candidates.index(end_key)
        # Both directions are accepted ("A9s-A5s" and "A5s-A9s" mean the same run) because tools in
        # the wild disagree. A notation that silently produced a different range would be worse.
        lo, hi = sorted((position, end_position))
        return [(key, frequency) for key in candidates[lo : hi + 1]]

    if plus:
        return [(key, frequency) for key in candidates[position:]]

    if shape is None:
        # A bare "AK" means both suited and offsuit, matching how players actually write it.
        return [(anchor, frequency), (f"{high}{low}o", frequency)]
    return [(anchor, frequency)]


def parse(spec: str, *, exclude: Sequence[Card] = ()) -> Range:
    """``"22+, ATs+, KJo+"`` -> Range. Unknown tokens raise with the offending token named.

    ``exclude`` is not a convenience. A range described *after a flop has been dealt* cannot contain a
    combo using a board card, yet the 169-class notation has no way to say that: "77" on
    ``Kh7s3d`` is written the same way as "77" preflop. Without this parameter the only defence was to
    remember to chain :meth:`pokergto.ranges.Range.with_removed` at every call site, and the nut-share
    figures in ``table.03-01`` and ``table.03-02`` were computed exactly that way -- hero's share read
    0.1154 where the physical combos give 0.0682, because six combos of the eight that were counted
    cannot be dealt. Defaulting to ``()`` keeps every preflop use identical, so the safe case stays the
    one that needs no thought.
    """
    cleaned = []
    for line in spec.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";") or stripped.startswith("["):
            continue
        cleaned.append(stripped)
    text = ",".join(cleaned)
    entries: dict[str, float] = {}
    for token in re.split(r"[,\s]+", text):
        for key, frequency in _expand(token):
            previous = entries.get(key, 0.0)
            if frequency < previous:
                raise NotationError(
                    f"{key} is specified twice with conflicting frequencies "
                    f"({previous} then {frequency}); intersection semantics are not implied here"
                )
            entries[key] = max(previous, frequency)
    if not entries:
        raise NotationError(f"range spec {spec!r} is empty")
    rng = Range.from_classes(entries)
    return rng.with_removed(*exclude) if exclude else rng


def expand(spec: str) -> list[tuple[str, int]]:
    """Class keys with their combo counts, in canonical 169 order. The quantity a lesson calls
    'how many combos do I have for this line'.
    """
    rng = parse(spec)
    return sorted(
        ((key, combos_for_class(key)) for key in rng.frequency_map()),
        key=lambda item: _class_sort_key(item[0]),
    )


def _class_sort_key(key: str) -> tuple[int, int, int]:
    high = _RANK_INDEX[key[0]]
    low = _RANK_INDEX[key[1]]
    shape = 0 if len(key) == 2 else (1 if key[2] == "s" else 2)
    return (shape, high, low)


def to_spec(rng: Range, *, lossy: bool = False) -> str:
    """A minimal human-readable spec.

    Strict mode (default) guarantees that ``parse(to_spec(rng))`` equals ``rng``. If that is not
    achievable it raises :class:`NotationError` rather than quietly returning a different range:
    a chart that round-trips to something else is a documentation bug wearing a string.
    """
    frequencies = rng.frequency_map()
    if not frequencies:
        raise NotationError("cannot render an empty range as a spec")

    # Detect sub-combo precision: a class whose weight is not a multiple of 1/combos cannot be
    # expressed at all, even lossily, without changing which physical combos are in it.
    for key, frequency in frequencies.items():
        combos = combos_for_class(key)
        scaled = frequency * combos
        if abs(scaled - round(scaled)) > 1e-9 and not lossy:
            raise NotationError(
                f"{key} has frequency {frequency}, which is not a whole number of its {combos} "
                f"combos. Pass lossy=True to render the class-level approximation."
            )

    # Group by (high card, shape, frequency). Frequency is part of the key because merging a full
    # class with a half-included one into a single run would silently invent a range.
    groups: dict[tuple[str, str, float], set[str]] = {}
    for key, frequency in sorted(frequencies.items()):
        rounded = round(frequency, 12)
        if len(key) == 2:
            # All thirteen pairs share one "high card" slot, otherwise each pair would be its own
            # group and "AA-77" would render as thirteen separate tokens.
            groups.setdefault(("_pair", "pair", rounded), set()).add(key[0])
        else:
            groups.setdefault((key[0], key[2], rounded), set()).add(key[1])

    parts: list[str] = []
    for (high, shape, frequency), partners in sorted(
        groups.items(),
        key=lambda item: (item[0][1] != "pair", _RANK_INDEX.get(item[0][0], -1), -item[0][2]),
    ):
        # A fractional frequency is emitted per class ("AKs:0.5,AOs:0.5") rather than as a run,
        # because "AJs-AKs:0.5" is not syntax any tool in the wild recognises, and inventing a
        # dialect here would break the one job a notation has: round-tripping.
        if frequency != 1.0:
            if shape == "pair":
                parts.extend(
                    f"{p}{p}:{frequency:g}" for p in sorted(partners, key=_RANK_INDEX.__getitem__)
                )
            else:
                parts.extend(
                    f"{high}{p}{shape}:{frequency:g}"
                    for p in sorted(partners, key=_RANK_INDEX.__getitem__)
                )
            continue

        if shape == "pair":
            indices = sorted(_RANK_INDEX[p] for p in partners)
            if indices == list(range(len(_RANKS))):
                parts.append("22+")
                continue
            if indices == list(range(max(indices) + 1)):
                # Contiguous from aces down: "TT+" style, named by the lowest included pair.
                parts.append(f"{_RANKS[max(indices)]}{_RANKS[max(indices)]}+")
                continue
            parts.append(
                f"{_RANKS[min(indices)]}{_RANKS[min(indices)]}-{_RANKS[max(indices)]}{_RANKS[max(indices)]}"
            )
            continue

        indices = sorted(_RANK_INDEX[p] for p in partners)
        for run in _runs(indices):
            parts.append(_render_run(high, shape, run))

    spec = ",".join(parts)
    if not lossy:
        round_tripped = parse(spec)
        if not round_tripped.equal(rng):
            raise NotationError(
                f"strict round-trip failed: {spec!r} re-parses to a different range "
                f"(differing classes: {sorted(set(round_tripped.frequency_map()) ^ set(frequencies))} "
                f"or mismatched frequencies)"
            )
    return spec


def _render_run(high: str, shape: str, run: tuple[int, int]) -> str:
    top_rank, bottom_rank = _RANKS[run[0]], _RANKS[run[1]]
    if run[1] == len(_RANKS) - 1:
        return f"{high}{top_rank}{shape}+"
    if run[0] == run[1]:
        return f"{high}{top_rank}{shape}"
    return f"{high}{top_rank}{shape}-{high}{bottom_rank}{shape}"


def _runs(indices: list[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    start = previous = indices[0]
    for value in indices[1:]:
        if value == previous + 1:
            previous = value
            continue
        out.append((start, previous))
        start = previous = value
    out.append((start, previous))
    return out


def grid_axis() -> list[str]:
    """The 13 axis labels shared by every chart, so docs, engine and trainer cannot disagree."""
    return [r.char for r in GRID_RANKS]
