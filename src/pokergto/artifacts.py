"""Artifact I/O: the only place that decides how a number is written down.

Determinism is a contract, not a preference (ADR-0001). Two runs on two machines must produce
byte-identical JSON, otherwise ``tools/gen_all.py --check`` is noise and every solver tweak looks
like a thousand-line diff. So:

* keys sorted, ``ensure_ascii=False`` (Chinese stays readable, not ``\\u4e2d``), two-space indent,
  trailing newline, LF endings;
* floats quantised to 12 decimals before dumping, so a platform-specific last bit cannot leak into
  a diff;
* **no timestamps inside artifact bodies** — a generated file's content is a function of its inputs
  and nothing else. Build provenance lives in ``manifest.json`` metadata instead, and even there it
  is recorded as ``git_sha``/versions rather than a clock;
* every artifact validates against ``data/schema/*.json`` on both write and read, so a corrupt file
  fails loudly at the boundary instead of halfway through a lesson build.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator

from .errors import ProvenanceError, SchemaDriftError

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schema"
SRC_DIR = DATA_DIR / "src"
GEN_DIR = DATA_DIR / "gen"
DOCS_DIR = REPO_ROOT / "docs"

#: Decimal places kept for every generated float. Twelve is far beyond any poker claim and short
#: enough that 1/3 does not dominate a diff.
FLOAT_DIGITS = 12


def quantize(value: float, digits: int = FLOAT_DIGITS) -> float:
    return round(float(value), digits)


def _prepare(payload: Any, *, digits: int = FLOAT_DIGITS) -> Any:
    if isinstance(payload, float):
        return quantize(payload, digits)
    if isinstance(payload, Mapping):
        return {str(key): _prepare(value, digits=digits) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_prepare(value, digits=digits) for value in payload]
    return payload


def dumps(payload: Any, *, digits: int = FLOAT_DIGITS) -> str:
    """Canonical JSON text. The single serialisation path every generator must use."""
    return json.dumps(_prepare(payload, digits=digits), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def dump_bytes(payload: Any) -> bytes:
    return dumps(payload).encode("utf-8")


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_file(path: Path) -> str:
    return sha256_of(path.read_bytes())


def write_artifact(path: Path, payload: Mapping[str, Any], *, schema: str | None = None) -> str:
    """Validate then write. Returns the sha256 so callers can build a manifest without re-reading."""
    data = dict(payload)
    if schema is not None:
        validate_artifact(data, schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dumps(data)
    path.write_text(text, encoding="utf-8", newline="\n")
    return sha256_of(text.encode("utf-8"))


def read_artifact(path: Path, *, schema: str | None = None) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if schema is not None:
        validate_artifact(data, schema)
    return data


_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


def load_schema(name: str) -> dict[str, Any]:
    key = name if name.endswith(".json") else f"{name}.schema.json"
    if key not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[key] = json.loads((SCHEMA_DIR / key).read_text(encoding="utf-8"))
    return _SCHEMA_CACHE[key]


def _registry():
    """Local registry over ``data/schema`` so cross-file ``$ref`` resolves without network access.

    ``$ref: "common.schema.json#/$defs/provenance"`` is resolved relative to the referring schema's
    ``$id``, which is why every schema in this directory declares one. Nothing here performs I/O:
    a docs build with no network must still validate, and a validator that phoned home would be both
    slow and a privacy problem (see SECURITY.md).
    """
    from referencing import Registry
    from referencing.jsonschema import DRAFT202012

    resources = []
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        uri = schema.get("$id")
        if uri is None:  # pragma: no cover - every schema declares its $id
            raise SchemaDriftError(f"{path.name} has no $id, so its $refs cannot resolve")
        resources.append((uri, DRAFT202012.create_resource(schema)))
    return Registry().with_resources(resources)


def validate_artifact(data: Mapping[str, Any], schema: str) -> None:
    """Raise :class:`SchemaDriftError` on a violation, :class:`ProvenanceError` on provenance ones."""
    validator = Draft202012Validator(load_schema(schema), registry=_registry())
    errors = sorted(validator.iter_errors(dict(data)), key=lambda err: list(err.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "<root>"
        kind = ProvenanceError if "provenance" in location else SchemaDriftError
        raise kind(f"{schema} violation at {location}: {first.message}")


# --- provenance helpers ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Provenance:
    """Builder for the required ``provenance`` block.

    Three constructors, one per ``kind``, so a call site cannot forget to say where a number came
    from. ``verified`` stays ``False`` until something checkable is attached, which is the whole
    content of ADR-0005 in fifteen lines of Python.
    """

    kind: str
    license: str = "CC-BY-SA-4.0"
    upstream: str | None = None
    derivation_ref: str | None = None
    solver_run: str | None = None
    confidence: str = "medium"
    verified: bool = False
    assumptions: list[dict[str, str]] = field(default_factory=list)
    note: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "license": self.license,
            "upstream": self.upstream,
            "derivation_ref": self.derivation_ref,
            "solver_run": self.solver_run,
            "confidence": self.confidence,
            "verified": self.verified,
            "assumptions": list(self.assumptions),
            # Omitted rather than written as null: `note` is a lang_string in the schema, and a
            # provenance block that claims to have a note of type null is noise a reviewer skips.
            **({"note": self.note} if self.note is not None else {}),
        }

    @classmethod
    def derived(
        cls, derivation_ref: str, *, solver_run: str | None = None, verified: bool = True,
        confidence: str = "high", assumptions: Sequence[str] = (), note: dict[str, str] | None = None,
    ) -> Provenance:
        return cls(
            kind="derived",
            derivation_ref=derivation_ref,
            solver_run=solver_run,
            verified=verified,
            confidence=confidence if verified else "medium",
            assumptions=[{"zh": text, "en": text} for text in assumptions],
            note=note,
        )

    @classmethod
    def reference(
        cls, note: dict[str, str], *, confidence: str = "medium",
        assumptions: Sequence[str] = (),
    ) -> Provenance:
        return cls(
            kind="reference",
            confidence=confidence,
            verified=False,
            assumptions=[{"zh": text, "en": text} for text in assumptions],
            note=note,
        )

    @classmethod
    def external(cls, upstream: str, license: str, note: dict[str, str], *, confidence: str = "medium") -> Provenance:
        return cls(
            kind="external", upstream=upstream, license=license, note=note,
            confidence=confidence, verified=False,
        )


def unverified_claim(zh: str, en: str, why_zh: str, why_en: str, path_zh: str, path_en: str) -> dict[str, Any]:
    """A claim that is honest about not being proven yet. Rendered as a badge in both languages."""
    return {
        "claim": {"zh": zh, "en": en},
        "why_unverified": {"zh": why_zh, "en": why_en},
        "path_to_verified": {"zh": path_zh, "en": path_en},
        "blocks_ready_status": False,
    }


def manifest_entry(kind: str, path: Path, relative_to: Path | None = None, *, schema: str | None = None) -> dict[str, Any]:
    target = path.relative_to(relative_to or GEN_DIR).as_posix()
    payload = {
        "kind": kind,
        "sha256": sha256_of_file(path),
        "bytes": path.stat().st_size,
        "schema": schema,
    }
    return {"path": target, **payload}


def write_manifest(
    files: Iterable[tuple[str, Path, str | None]],
    *,
    engine_version: str,
    schema_version: str,
    git_sha: str | None = None,
    root: Path | None = None,
) -> Path:
    """``data/gen/manifest.json``: the fingerprint of a generated tree.

    Deliberately excludes its own hash and any clock value, so the manifest can be byte-stable
    across rebuilds of unchanged inputs.
    """
    import sys

    base = root or GEN_DIR
    entries: dict[str, Any] = {}
    for kind, path, schema in files:
        relative = path.relative_to(base).as_posix()
        entries[relative] = {
            "kind": kind,
            "sha256": sha256_of_file(path),
            "bytes": path.stat().st_size,
            "schema": schema,
        }
    payload = {
        "schema_version": schema_version,
        "engine_version": engine_version,
        "generator": "tools/gen_all.py",
        "python": ".".join(str(part) for part in sys.version_info[:3]),
        "numpy": _numpy_version(),
        "git_sha": git_sha,
        "artifact_count": len(entries),
        "files": entries,
    }
    path = base / "manifest.json"
    write_artifact(path, payload, schema="manifest")
    return path


def _numpy_version() -> str | None:
    try:
        import numpy

        return numpy.__version__
    except Exception:  # pragma: no cover - numpy is a hard dependency
        return None
