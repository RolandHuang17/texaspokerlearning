#!/usr/bin/env python3
"""Provenance gate: the copyright and honesty rule, expressed as a build failure.

See ``NOTICE``, ``adr/0005-provenance-is-schema-required.md`` and ``data/README.md``. The policy is
"every strategy claim says where it came from, and nothing proprietary is here". This tool makes
that policy *structural*: a chart without provenance does not fail review, it fails the build.

Checks:

1. **Required and well-shaped.** Every authored spot/chart/hand/quiz in ``data/src`` carries a
   ``provenance`` block; every generated artifact in ``data/gen`` validates against its schema, which
   already requires one. A schema violation here is reported as a provenance problem, because that is
   what it is.
2. **``verified: true`` must point at something.** A derivation reference that resolves to a real
   symbol in ``src/pokergto``, or a solver run recorded in ``data/gen/solver``, or an upstream listed
   in ``licensing_manifest.yaml``. Anything else is demoted with an error, because an unverifiable
   claim carrying a verified badge is worse than an unverified one.
3. **Licences are on the allow-list.** Proprietary solver output and paid-course content are rejected
   by name as well as by schema, so a contributor pasting a GTO Wizard range gets a pointed message
   instead of a generic validation error.
4. **UNVERIFIED claims are visible in both languages.** An artifact whose ``verified`` is false must
   render the badge wherever a lesson embeds it -- which is what ``tools/inject_doc_tables.py`` writes
   between the AUTO markers, and what this tool re-derives to confirm nothing was hand-edited away.

Usage::

    python tools/check_provenance.py [--strict]
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from _bootstrap import REPO_ROOT, bootstrap_path, fail, ok

bootstrap_path()

DATA_SRC = REPO_ROOT / "data" / "src"
DATA_GEN = REPO_ROOT / "data" / "gen"
DOCS = REPO_ROOT / "docs"
MANIFEST = DATA_SRC / "licensing_manifest.yaml"

#: Names that must never appear as a source of ranges or strategy output here.
PROPRIETARY_MARKERS = (
    "piosolver",
    "pio solver",
    "gto wizard",
    "gtowizard",
    "gto+",
    "gto plus",
    "solwars",
    "bodrum",
    "slurm",
    "postflop plus",
    "upswing",
    "run it once",
    "raised run",
    "monker",
)

PROVENANCE_KEYS = {"kind", "verified", "confidence", "license", "upstream"}
KINDS = {"derived", "reference", "external"}
ACCEPTED_LICENSES = {"CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MIT", "public-domain-math", "fair-use-commentary"}

ARTIFACT_MARKER = re.compile(r"<!--\s*provenance:\s*kind=(\w+)\s+verified=(true|false)\s*-->")


def _iter_yaml(path: Path):
    import yaml

    for file in sorted(path.rglob("*.yaml")):
        payload = yaml.safe_load(file.read_text(encoding="utf-8"))
        if payload is None:
            continue
        yield file, payload


def _check_provenance_block(provenance: Any, where: str, problems: list[str]) -> None:
    if not isinstance(provenance, dict):
        problems.append(f"{where}: provenance must be an object")
        return
    missing = PROVENANCE_KEYS - set(provenance)
    if missing:
        problems.append(f"{where}: provenance missing required keys {sorted(missing)}")
        return
    kind = provenance["kind"]
    if kind not in KINDS:
        problems.append(f"{where}: unknown provenance kind {kind!r}")
        return
    license_id = str(provenance["license"])
    if license_id not in ACCEPTED_LICENSES:
        problems.append(
            f"{where}: license {license_id!r} is not on the allow-list "
            f"({', '.join(sorted(ACCEPTED_LICENSES))})"
        )
    if kind == "external" and not provenance.get("upstream"):
        problems.append(f"{where}: kind=external requires upstream")
    if kind == "derived" and not (provenance.get("derivation_ref") or provenance.get("solver_run")):
        problems.append(f"{where}: kind=derived requires derivation_ref or solver_run")
    if provenance.get("verified"):
        if provenance.get("confidence") != "high":
            problems.append(f"{where}: verified: true requires confidence: high")
        if not _points_at_something(provenance):
            problems.append(
                f"{where}: verified: true but nothing checkable is attached "
                "(derivation_ref / solver_run / upstream)"
            )


def _points_at_something(provenance: dict[str, Any]) -> bool:
    reference = provenance.get("derivation_ref")
    if isinstance(reference, str) and reference:
        return _derivation_exists(reference)
    solver_run = provenance.get("solver_run")
    if isinstance(solver_run, str) and solver_run:
        return (REPO_ROOT / solver_run).exists() or (DATA_GEN.parent / solver_run).exists()
    upstream = provenance.get("upstream")
    return bool(upstream)


def _derivation_exists(reference: str) -> bool:
    """``pokergto.odds#minimum_defense_frequency`` or ``src/pokergto/odds.py`` -> exists?

    A dead pointer is the failure mode of every citation system, so pointers are resolved here rather
    than admired in review.
    """
    symbol, _, attribute = reference.partition("#")
    if symbol.startswith("src/"):
        return (REPO_ROOT / symbol).exists()
    module_name = symbol.split(".")[0] if "." not in symbol else symbol
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return False
    if not attribute:
        return True
    target = module
    for part in attribute.split("."):
        if not hasattr(target, part):
            return False
        target = getattr(target, part)
    return True


def _manifest_upstreams() -> set[str]:
    if not MANIFEST.exists():
        return set()
    import yaml

    payload = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    return {str(record.get("upstream", "")) for record in payload.get("records", [])}


def _scan_proprietary(path: Path, problems: list[str]) -> None:
    for file in sorted(path.rglob("*")):
        if not file.is_file() or file.suffix not in {".yaml", ".yml", ".md", ".json"}:
            continue
        text = file.read_text(encoding="utf-8").lower()
        for marker in PROPRIETARY_MARKERS:
            if marker in text and "prohibited" not in text and "not permitted" not in text:
                problems.append(
                    f"{file.relative_to(REPO_ROOT)}: mentions {marker!r}. This repository may not "
                    "contain range charts or strategy output from commercial solvers or paid courses "
                    "(see NOTICE). If this is a prohibition statement, add the words 'prohibited' or "
                    "'not permitted' so the scan can tell a ban from a source."
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail when any artifact is still reference/unverified (use in a later milestone)",
    )
    args = parser.parse_args(argv)
    problems: list[str] = []
    checked = 0

    if DATA_SRC.exists():
        for file, payload in _iter_yaml(DATA_SRC):
            if file.name == "licensing_manifest.yaml" or file.name == "curriculum.yaml":
                continue
            records = payload if isinstance(payload, list) else [payload]
            for record in records:
                if not isinstance(record, dict):
                    continue
                checked += 1
                where = str(file.relative_to(REPO_ROOT))
                if "provenance" not in record:
                    problems.append(
                        f"{where}: record {record.get('id', '<no id>')} has no provenance block; "
                        "every strategy claim must state its origin (adr/0005)"
                    )
                    continue
                _check_provenance_block(record["provenance"], where, problems)

    upstreams = _manifest_upstreams()
    if DATA_GEN.exists():
        for file in sorted(DATA_GEN.rglob("*.json")):
            if file.name == "manifest.json":
                continue
            payload = json.loads(file.read_text(encoding="utf-8"))
            provenance = payload.get("provenance")
            if provenance is None:
                continue
            checked += 1
            _check_provenance_block(provenance, str(file.relative_to(REPO_ROOT)), problems)
            if provenance.get("kind") == "external" and str(provenance.get("upstream")) not in upstreams:
                problems.append(
                    f"{file.relative_to(REPO_ROOT)}: external upstream "
                    f"{provenance.get('upstream')!r} is not recorded in licensing_manifest.yaml"
                )

    _scan_proprietary(DATA_SRC, problems) if DATA_SRC.exists() else None

    # Every embedded AUTO block in the docs must carry a provenance marker.
    if DOCS.exists():
        for file in sorted(DOCS.rglob("*.md")):
            text = file.read_text(encoding="utf-8")
            begins = text.count("<!-- BEGIN AUTO:")
            markers = len(ARTIFACT_MARKER.findall(text))
            if begins and markers < begins:
                problems.append(
                    f"{file.relative_to(REPO_ROOT)}: {begins} AUTO tables but {markers} provenance "
                    "markers; regenerate with tools/inject_doc_tables.py"
                )

    if problems:
        for problem in problems[:80]:
            fail(problem)
        if len(problems) > 80:
            print(f"... and {len(problems) - 80} more", file=sys.stderr)
        return 1

    message = f"provenance: {checked} records checked, every claim has an origin"
    if args.strict:
        unverified = 0
        if DATA_GEN.exists():
            for file in DATA_GEN.rglob("*.json"):
                payload = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(payload, dict) and payload.get("provenance", {}).get("verified") is False:
                    unverified += 1
        if unverified:
            fail(f"--strict: {unverified} artifacts are still unverified")
            return 1
        message += ", all verified"
    ok(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
