"""Rendering: how a number or a grid becomes text in two languages, identically.

Three hazards live here, and each has a deliberate answer:

1. **CJK tables render as ragged garbage on GitHub.** Markdown tables align by *display* width, and
   a Chinese character occupies two cells in a monospace view while counting as one Python character.
   :func:`display_width` uses ``unicodedata.east_asian_width`` and every padded renderer goes through
   it, so ``docs/zh`` tables line up instead of limping.
2. **Units drift between languages.** They cannot: values are rendered from ``numeric_value`` objects
   carrying a unit, and both locales read the same field.
3. **An UNVERIFIED claim that looks like a proven one.** :func:`provenance_block` renders the badge
   from artifact metadata rather than from prose, so a chart's honesty travels with the chart.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any, cast

from .matrix13 import AXIS, ORIENTATION, Grid13

#: Fill characters for a frequency grid. Five bands, stated as bands so a learner reading a printed
#: chart knows exactly what a shade means instead of guessing at a gradient.
FILL_BANDS: tuple[tuple[float, str], ...] = (
    (0.0, "."),
    (0.01, "-"),
    (0.34, ":"),
    (0.67, "+"),
    (0.9, "#"),
    (1.01, "@"),
)


def display_width(text: str) -> int:
    """Monospace display columns, counting East Asian wide characters as two."""
    return sum(2 if unicodedata.east_asian_width(char) in ("W", "F") else 1 for char in text)


def pad(text: str, width: int, *, align: str = "left") -> str:
    missing = max(0, width - display_width(text))
    if align == "right":
        return " " * missing + text
    if align == "center":
        left = missing // 2
        return " " * left + text + " " * (missing - left)
    return text + " " * missing


def fill_for(frequency: float) -> str:
    for threshold, glyph in FILL_BANDS:
        if frequency < threshold:
            return glyph
    return "@"


def markdown_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    *,
    align: Sequence[str] | None = None,
) -> str:
    """A GitHub-friendly markdown table, padded by display width so Chinese headers align."""
    columns = len(headers)
    align = list(align or ["left"] * columns)
    grid = [list(headers)] + [list(row) for row in rows]
    widths = [
        max(display_width(str(cell)) for cell in column) for column in zip(*grid, strict=False)
    ]
    lines = [
        "| "
        + " | ".join(pad(str(headers[i]), widths[i], align=align[i]) for i in range(columns))
        + " |",
        "|"
        + "|".join(
            ("---:" if align[i] == "right" else ":---:" if align[i] == "center" else "---")
            for i in range(columns)
        )
        + "|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(pad(str(row[i]), widths[i], align=align[i]) for i in range(columns))
            + " |"
        )
    return "\n".join(lines)


def table_from_artifact(artifact: Mapping[str, Any], *, locale: str = "en") -> str:
    """Render a ``table`` artifact for insertion into a lesson.

    Cells may be plain scalars or ``{value, unit}`` objects; both are formatted here so no generator
    has to think about presentation, and no translator has to retype a number.
    """
    columns = list(artifact["columns"])
    headers = [str(column["header"][locale]) for column in columns]
    align = ["right" if column.get("unit") != "ratio" else "center" for column in columns]
    rows: list[list[str]] = []
    for raw in artifact["rows"]:
        cells: list[str] = []
        for column in columns:
            cell = raw.get(column["key"])
            cells.append(_format_cell(cell, column, locale=locale))
        rows.append(cells)
    return markdown_table(headers, rows, align=align)


def _format_cell(cell: Any, column: Mapping[str, Any], *, locale: str) -> str:
    """Render one table cell.

    The column carries the unit when the row carries a bare number, because generated tables store
    plain floats for compactness and the unit lives in the column definition. Handling a string cell
    *before* the numeric path matters: without that order, a text column like ``size_label`` reaches
    the float formatting and silently renders as ``0``.
    """
    if isinstance(cell, Mapping) and "value" in cell:
        unit = str(cell.get("unit", column.get("unit", "dimensionless")))
        value = float(cast(float, cell["value"]))
        return _format_number(value, unit, int(column.get("digits", 2)))
    if isinstance(cell, bool):
        return ("yes" if cell else "no") if locale == "en" else ("是" if cell else "否")
    if cell is None:
        return "-"
    if isinstance(cell, str):
        return cell
    if isinstance(cell, (int, float)):
        return _format_number(
            float(cell), str(column.get("unit", "dimensionless")), int(column.get("digits", 2))
        )
    return str(cell)


def _format_number(value: float, unit: str, digits: int) -> str:
    if unit == "probability":
        return f"{100 * value:.{digits}f}%"
    if unit == "percent":
        return f"{value:.{digits}f}%"
    if unit == "ratio":
        return f"{value:.{digits}g} : 1"
    suffix = {
        "bb": " bb",
        "bb_per_100": " bb/100",
        "combos": " combos",
        "hands": " hands",
        "chips_per_hand": " chips",
    }.get(unit, "")
    if unit in ("dimensionless", "") and not suffix:
        return f"{value:g}"
    return f"{value:.{digits}f}{suffix}"


def grid_to_text(grid: Grid13, *, locale: str = "en") -> str:
    """Fixed-width 13x13 render for terminals and CLI output."""
    lines = ["     " + " ".join(f"{label:<2}" for label in AXIS)]
    for row, label in enumerate(AXIS):
        cells = []
        for col in range(13):
            frequency = float(grid.values[row, col])
            cells.append(fill_for(frequency) * 2 if frequency >= 0.01 else "..")
        lines.append(f"{label:<4} " + " ".join(cells))
    if locale == "zh":
        lines.append("图例: .. <1%  :: 1-34%  ++ 34-67%  ## 67-90%  @@ >90%")
    else:
        lines.append("legend: .. <1%  :: 1-34%  ++ 34-67%  ## 67-90%  @@ >90%")
    return "\n".join(lines)


def grid_to_svg(grid: Grid13, *, cell: int = 34, gap: int = 2, locale: str = "en") -> str:
    """Standalone SVG for a range chart. No external assets, no script, safe to embed.

    Colour encodes frequency bands rather than a smooth gradient, so the printed chart and the
    screen chart communicate the same thresholds.
    """
    size = 13 * (cell + gap) + gap + 40
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" role="img">',
        f'<rect width="{size}" height="{size}" fill="#1b1a17"/>',
    ]
    for row in range(13):
        for col in range(13):
            frequency = float(grid.values[row, col])
            shade = _shade(frequency)
            x = 40 + col * (cell + gap)
            y = 40 + row * (cell + gap)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{shade}"/>')
            if frequency >= 0.01:
                parts.append(
                    f'<text x="{x + cell / 2:.1f}" y="{y + cell / 2 + 4:.1f}" fill="#0d0d0c" '
                    f'font-size="10" font-family="monospace" text-anchor="middle">'
                    f"{AXIS[row]}{AXIS[col] if row != col else ''}"
                    f"{'s' if col > row else 'o' if col < row else ''}</text>"
                )
    for index, label in enumerate(AXIS):
        parts.append(
            f'<text x="{40 + index * (cell + gap) + cell / 2:.1f}" y="32" fill="#e8e6e3" '
            f'font-size="12" font-family="monospace" text-anchor="middle">{label}</text>'
        )
        parts.append(
            f'<text x="30" y="{40 + index * (cell + gap) + cell / 2 + 4:.1f}" fill="#e8e6e3" '
            f'font-size="12" font-family="monospace" text-anchor="middle">{label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


_SHADES = ("#2a2a2c", "#4a6b8a", "#7fa8c9", "#c9b26a", "#e08b4f", "#d94f4f")


def _shade(frequency: float) -> str:
    if frequency < 0.01:
        return _SHADES[0]
    return _SHADES[min(len(_SHADES) - 1, int(frequency * (len(_SHADES) - 1)) + 1)]


def chart_to_markdown(artifact: Mapping[str, Any], *, locale: str = "en") -> str:
    """A 13x13 chart as a markdown table of frequency bands.

    A table rather than an image because it must be diffable in a pull request, readable in a
    terminal, and identical in both languages. The bands are :data:`FILL_BANDS`, and the legend line
    states their thresholds, so a printed page explains itself.
    """
    from .matrix13 import AXIS, Grid13

    grid = Grid13.from_chart(artifact)
    headers = [""] + list(AXIS)
    rows: list[list[str]] = []
    for row, label in enumerate(AXIS):
        cells = [label]
        for col in range(13):
            frequency = float(grid.values[row, col])
            cells.append(
                fill_for(frequency) * 2 if frequency >= 0.01 else "··" if locale == "zh" else ".."
            )
        rows.append(cells)
    legend = (
        "图例：`··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%；"
        "对角线为对子，上三角同花，下三角不同花。"
        if locale == "zh"
        else "Legend: `··` <1% · `::` 1-34% · `++` 34-67% · `##` 67-90% · `@@` >90%; "
        "the diagonal is pairs, the upper triangle suited, the lower offsuit."
    )
    width = float(artifact.get("range_percentage", grid.range_percentage()))
    if locale == "zh":
        stat = f"覆盖 {grid.combos():.1f} 组合 = 全 1326 的 {width:.2f}%"
    else:
        stat = f"{grid.combos():.1f} combos = {width:.2f}% of all 1,326"
    return "\n\n".join([markdown_table(headers, rows, align=["center"] * 14), stat, legend])


def provenance_block(provenance: Mapping[str, Any], *, locale: str = "en") -> str:
    """The honesty footer under every chart and table, generated from metadata.

    mkdocs-material renders ``!!!`` as an admonition; on GitHub the fenced block still reads. The
    class name ``unverified`` is asserted by ``tools/check_provenance.py`` so the badge cannot be
    quietly dropped from a template.
    """
    kind = str(provenance.get("kind", "reference"))
    verified = bool(provenance.get("verified", False))
    confidence = str(provenance.get("confidence", "medium"))
    if locale == "zh":
        label = {
            "derived": "本仓库推导",
            "reference": "作者自建的参考范围",
            "external": "外部来源",
        }[kind]
        state = "已核验" if verified else "未核验"
        note = provenance.get("note") or {}
        extra = f"：{note.get('zh')}" if note.get("zh") else ""
        return f'!!! unverified "来源：{label} · {state} · 置信度 {confidence}{extra}"\n    推导位置：`{provenance.get("derivation_ref") or provenance.get("solver_run") or provenance.get("upstream") or "未给出"}`'
    label = {
        "derived": "derived in this repository",
        "reference": "author reference chart",
        "external": "external source",
    }[kind]
    state = "verified" if verified else "UNVERIFIED"
    note = provenance.get("note") or {}
    extra = f": {note.get('en')}" if note.get("en") else ""
    return (
        f'!!! unverified "Provenance: {label} · {state} · confidence {confidence}{extra}"\n'
        f"    Derived at: `{provenance.get('derivation_ref') or provenance.get('solver_run') or provenance.get('upstream') or 'not stated'}`"
    )


def render_chart_artifact(
    *,
    artifact_id: str,
    title: Mapping[str, str],
    grid: Grid13,
    provenance: Mapping[str, Any],
    spot: str | None = None,
    player: str | None = None,
    street: str = "n-a",
) -> dict[str, Any]:
    """Assemble a ``range_chart`` payload from a Grid13, with combo counts taken from module
    constants rather than trusting any caller.
    """
    if grid.to_numpy().shape != (13, 13):  # pragma: no cover - Grid13 enforces this
        raise ValueError("grid must be 13x13")
    payload = grid.to_chart()
    return {
        "schema_version": "1.0.0",
        "id": artifact_id,
        "title": dict(title),
        "spot": spot,
        "player": player,
        "street": street,
        "orientation": ORIENTATION,
        "rows": list(AXIS),
        "columns": list(AXIS),
        "cell_combos": payload["cell_combos"],
        "weights": payload["weights"],
        "total_combos": grid.combos(),
        "range_percentage": grid.range_percentage(),
        "provenance": dict(provenance),
    }
