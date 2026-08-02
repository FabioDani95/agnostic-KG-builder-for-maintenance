#!/usr/bin/env python3
"""Validate the normative MVP specification package and planning readiness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import jsonschema as _jsonschema
except ImportError:  # pragma: no cover - exercised through monkeypatch in tests
    _jsonschema = None

ROOT = Path(__file__).resolve().parent.parent
INDEX_RELATIVE_PATH = Path("docs/specs/SPEC_INDEX.json")
SCHEMA_RELATIVE_PATH = Path("docs/specs/SPEC_INDEX.schema.json")

DEFAULT_NORMATIVE_DOCUMENTS = (
    "SPECIFICHE_MVP.md",
    "docs/specs/UX_SPECIFICATION.md",
    "docs/specs/DATA_CONTRACTS.md",
    "docs/specs/DECISION_REGISTER.md",
    "docs/specs/BASELINE_AND_CODEBASE_IMPACT.md",
    "docs/specs/ACCEPTANCE_CRITERIA.md",
    "docs/specs/TRACEABILITY_MATRIX.md",
)

EXPECTED_ONTOLOGY_SHA256 = (
    "81f2d894e8b4c3c0ba3bb2e7149941ae91b704ebd8a8b8dedef91b79bd1508db"
)

HEADING_ID = re.compile(
    r"^#{2,6}\s+((?:INV|ACT|UC|FR|NFR|DC|AC|DS)-[A-Z0-9-]+)(?=\s|$)",
    re.MULTILINE,
)
REQUIREMENT_REFERENCE = re.compile(r"\b(?:INV|ACT|UC|FR|NFR)-[A-Z0-9-]+\b")
ACCEPTANCE_REFERENCE = re.compile(r"\bAC-[A-Z0-9-]+\b")
DECISION_ROW = re.compile(
    r"^\|\s*(DEC-\d{3})\s*\|\s*([A-Z_]+)\s*\|",
    re.MULTILINE,
)
JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
PLACEHOLDER = re.compile(
    r"^\s*(?:todo|tbd|to be defined|da definire|da decidere|n/?a|none|null|-)\s*$",
    re.IGNORECASE,
)

ID_PATTERNS = {
    "requirement": re.compile(
        r"^(?:(?:INV|ACT|UC)-\d{3}|(?:FR|NFR)(?:-[A-Z][A-Z0-9]*)*-\d{3})$"
    ),
    "contract": re.compile(r"^DC(?:-[A-Z][A-Z0-9]*)+-\d{3}$"),
    "acceptance": re.compile(r"^AC(?:-[A-Z][A-Z0-9]*)+-\d{3}$"),
    "dataset": re.compile(r"^DS(?:-[A-Z][A-Z0-9]*)*-\d{3}$"),
    "obligation": re.compile(r"^OBL-[A-Z0-9][A-Z0-9-]*$"),
    "verification": re.compile(r"^TST-[A-Z0-9][A-Z0-9-]*$"),
    "artifact": re.compile(r"^ART-[A-Z0-9][A-Z0-9-]*$"),
    "decision": re.compile(r"^DEC-\d{3}$"),
    "finding": re.compile(r"^AUD-\d{3}$"),
}

ACTIVE_ITEM_STATUSES = {"ACTIVE"}
TERMINAL_DECISION_STATUSES = {"ACCEPTED", "REJECTED", "SUPERSEDED"}
TERMINAL_FINDING_STATUSES = {"RESOLVED", "CLOSED"}
READINESS_STATUSES = {
    "NOT_READY",
    "AWAITING_OWNER_APPROVAL",
    "READY_FOR_PLANNING",
}


class DuplicateKeyError(ValueError):
    """Raised when strict JSON decoding encounters a duplicate object key."""


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    category: str = "consistency"
    path: str | None = None
    line: int | None = None

    def render(self) -> str:
        location = ""
        if self.path:
            location = self.path
            if self.line is not None:
                location += f":{self.line}"
            location += ": "
        return f"[{self.code}] {location}{self.message}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": self.category,
            "message": self.message,
            "path": self.path,
            "line": self.line,
        }


@dataclass(frozen=True)
class Definition:
    identifier: str
    kind: str
    path: str
    line: int


@dataclass(frozen=True)
class Inventory:
    definitions: tuple[Definition, ...]

    def ids(self, kind: str) -> set[str]:
        return {
            definition.identifier
            for definition in self.definitions
            if definition.kind == kind
        }

    def counts(self) -> dict[str, int]:
        return {
            kind: len(self.ids(kind))
            for kind in ("requirement", "contract", "acceptance", "dataset")
        }


@dataclass(frozen=True)
class Readiness:
    declared_status: str | None
    derived_status: str
    package_digest: str | None
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "declared_status": self.declared_status,
            "derived_status": self.derived_status,
            "package_digest": self.package_digest,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class Evaluation:
    issues: tuple[Issue, ...]
    inventory: Inventory
    readiness: Readiness
    index_present: bool

    def messages(self) -> list[str]:
        return [issue.render() for issue in self.issues]

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": not self.issues,
            "index_present": self.index_present,
            "inventory": self.inventory.counts(),
            "readiness": self.readiness.as_dict(),
            "issues": [issue.as_dict() for issue in self.issues],
        }


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def strict_json_loads(text: str) -> Any:
    """Load JSON while rejecting duplicate object keys at every nesting level."""

    return json.loads(text, object_pairs_hook=_strict_object)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _add_issue(
    issues: list[Issue],
    code: str,
    message: str,
    *,
    category: str = "consistency",
    path: str | None = None,
    line: int | None = None,
) -> None:
    issues.append(
        Issue(
            code=code,
            message=message,
            category=category,
            path=path,
            line=line,
        )
    )


def _safe_repo_path(
    root: Path,
    raw_path: Any,
    issues: list[Issue],
    *,
    code: str,
    context: str,
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        _add_issue(issues, code, f"{context} must be a non-empty repository-relative path.")
        return None

    candidate_value = Path(raw_path)
    if candidate_value.is_absolute():
        _add_issue(issues, code, f"{context} must not be absolute: {raw_path!r}.")
        return None

    root_resolved = root.resolve()
    candidate = (root / candidate_value).resolve()
    if not candidate.is_relative_to(root_resolved):
        _add_issue(issues, code, f"{context} escapes the repository: {raw_path!r}.")
        return None
    return candidate


def _kind_for_id(identifier: str) -> str | None:
    if ID_PATTERNS["requirement"].fullmatch(identifier):
        return "requirement"
    if ID_PATTERNS["contract"].fullmatch(identifier):
        return "contract"
    if ID_PATTERNS["acceptance"].fullmatch(identifier):
        return "acceptance"
    if ID_PATTERNS["dataset"].fullmatch(identifier):
        return "dataset"
    return None


def _normalise_status(value: Any) -> str:
    return str(value or "").strip().upper()


def _is_placeholder(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip() or bool(PLACEHOLDER.fullmatch(value))


def _records(
    index: dict[str, Any],
    key: str,
    issues: list[Issue],
) -> list[dict[str, Any]]:
    value = index.get(key)
    if not isinstance(value, list):
        _add_issue(issues, "IDX011", f"{key!r} must be an array.", path=INDEX_RELATIVE_PATH.as_posix())
        return []

    records: list[dict[str, Any]] = []
    for offset, record in enumerate(value):
        if not isinstance(record, dict):
            _add_issue(
                issues,
                "IDX012",
                f"{key}[{offset}] must be an object.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
            continue
        records.append(record)
    return records


def _registry(
    records: Iterable[dict[str, Any]],
    *,
    kind: str,
    issues: list[Issue],
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    pattern = ID_PATTERNS[kind]
    for offset, record in enumerate(records):
        identifier = record.get("id")
        if not isinstance(identifier, str) or not pattern.fullmatch(identifier):
            _add_issue(
                issues,
                "ID001",
                f"Invalid {kind} ID at position {offset}: {identifier!r}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
            continue
        if identifier in registry:
            _add_issue(
                issues,
                "ID002",
                f"Duplicate {kind} definition: {identifier}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
            continue
        registry[identifier] = record
    return registry


def _load_index(root: Path, issues: list[Issue]) -> dict[str, Any] | None:
    index_path = root / INDEX_RELATIVE_PATH
    if not index_path.exists():
        _add_issue(
            issues,
            "IDX001",
            "SPEC_INDEX.json is required for deterministic planning-readiness validation.",
            category="readiness",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )
        return None
    try:
        value = strict_json_loads(_read(index_path))
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        _add_issue(
            issues,
            "IDX002",
            f"Invalid strict JSON: {exc}.",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )
        return None
    if not isinstance(value, dict):
        _add_issue(
            issues,
            "IDX003",
            "The specification index root must be an object.",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )
        return None
    return value


def _fallback_schema_validation(index: dict[str, Any], issues: list[Issue]) -> None:
    required = {
        "schema_version": (str, int),
        "package": dict,
        "obligations": list,
        "verifications": list,
        "artifacts": list,
        "decisions": list,
        "findings": list,
        "readiness": dict,
    }
    for key, expected_type in required.items():
        if key not in index:
            _add_issue(
                issues,
                "SCH001",
                f"Missing required property {key!r}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
        elif not isinstance(index[key], expected_type):
            _add_issue(
                issues,
                "SCH002",
                f"Property {key!r} has the wrong type.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )

    package = index.get("package")
    if isinstance(package, dict):
        for key in ("spec_version", "normative_documents", "ontology"):
            if key not in package:
                _add_issue(
                    issues,
                    "SCH003",
                    f"package is missing required property {key!r}.",
                    path=INDEX_RELATIVE_PATH.as_posix(),
                )

    readiness = index.get("readiness")
    if isinstance(readiness, dict):
        for key in ("declared_status", "semantic_review", "owner_approval"):
            if key not in readiness:
                _add_issue(
                    issues,
                    "SCH004",
                    f"readiness is missing required property {key!r}.",
                    path=INDEX_RELATIVE_PATH.as_posix(),
                )


def _validate_schema(root: Path, index: dict[str, Any], issues: list[Issue]) -> None:
    schema_path = root / SCHEMA_RELATIVE_PATH
    if not schema_path.exists():
        _add_issue(
            issues,
            "SCH000",
            "SPEC_INDEX.schema.json is missing.",
            path=SCHEMA_RELATIVE_PATH.as_posix(),
        )
        _fallback_schema_validation(index, issues)
        return

    try:
        schema = strict_json_loads(_read(schema_path))
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        _add_issue(
            issues,
            "SCH005",
            f"Invalid strict JSON schema: {exc}.",
            path=SCHEMA_RELATIVE_PATH.as_posix(),
        )
        _fallback_schema_validation(index, issues)
        return

    if _jsonschema is None:
        _fallback_schema_validation(index, issues)
        return

    try:
        validator = _jsonschema.Draft202012Validator(schema)
        validation_errors = sorted(
            validator.iter_errors(index),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
    except Exception as exc:  # pragma: no cover - protects CLI from broken validator installs
        _add_issue(
            issues,
            "SCH006",
            f"Could not initialise JSON Schema validation: {exc}.",
            path=SCHEMA_RELATIVE_PATH.as_posix(),
        )
        _fallback_schema_validation(index, issues)
        return

    for error in validation_errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        _add_issue(
            issues,
            "SCH007",
            f"{location}: {error.message}",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )


def _normative_document_paths(
    root: Path,
    index: dict[str, Any],
    issues: list[Issue],
) -> list[Path]:
    package = index.get("package")
    if not isinstance(package, dict):
        return []
    documents = package.get("normative_documents")
    if not isinstance(documents, list):
        return []

    paths: list[Path] = []
    seen: set[Path] = set()
    for offset, document in enumerate(documents):
        raw_path = document.get("path") if isinstance(document, dict) else document
        path = _safe_repo_path(
            root,
            raw_path,
            issues,
            code="IDX020",
            context=f"package.normative_documents[{offset}]",
        )
        if path is None:
            continue
        if "archive" in path.relative_to(root.resolve()).parts:
            _add_issue(
                issues,
                "IDX021",
                f"Archived document cannot be normative: {_relative(path, root)}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
        if path in seen:
            _add_issue(
                issues,
                "IDX022",
                f"Duplicate normative document: {_relative(path, root)}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
            continue
        seen.add(path)
        paths.append(path)
        if not path.exists():
            _add_issue(
                issues,
                "IDX023",
                "Normative document does not exist.",
                path=_relative(path, root),
            )
    return paths


def _extract_inventory(
    root: Path,
    paths: Iterable[Path],
    issues: list[Issue],
) -> Inventory:
    definitions: list[Definition] = []
    for path in paths:
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        text = _read(path)
        relative = _relative(path, root)
        for match in HEADING_ID.finditer(text):
            identifier = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            kind = _kind_for_id(identifier)
            if kind is None:
                _add_issue(
                    issues,
                    "ID003",
                    f"Malformed normative heading ID: {identifier}.",
                    path=relative,
                    line=line,
                )
                continue
            definitions.append(
                Definition(
                    identifier=identifier,
                    kind=kind,
                    path=relative,
                    line=line,
                )
            )

    counts = Counter(definition.identifier for definition in definitions)
    locations: dict[str, list[str]] = defaultdict(list)
    for definition in definitions:
        locations[definition.identifier].append(f"{definition.path}:{definition.line}")
    for identifier, count in sorted(counts.items()):
        if count > 1:
            _add_issue(
                issues,
                "ID004",
                f"Duplicate normative heading {identifier}: {', '.join(locations[identifier])}.",
            )
    return Inventory(tuple(definitions))


def _validate_items(
    root: Path,
    index: dict[str, Any],
    inventory: Inventory,
    issues: list[Issue],
) -> tuple[set[str], set[str], set[str], set[str]]:
    inventory_by_id = {
        definition.identifier: definition for definition in inventory.definitions
    }
    active = {
        "requirement": set(inventory.ids("requirement")),
        "contract": set(inventory.ids("contract")),
        "acceptance": set(inventory.ids("acceptance")),
        "dataset": set(inventory.ids("dataset")),
    }

    if "items" not in index:
        return (
            active["requirement"],
            active["contract"],
            active["acceptance"],
            active["dataset"],
        )

    records = _records(index, "items", issues)
    seen: dict[str, dict[str, Any]] = {}
    for offset, item in enumerate(records):
        identifier = item.get("id")
        kind = item.get("kind")
        if not isinstance(identifier, str) or _kind_for_id(identifier) is None:
            _add_issue(
                issues,
                "ID005",
                f"items[{offset}] has an invalid normative ID: {identifier!r}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
            continue
        if identifier in seen:
            _add_issue(
                issues,
                "ID006",
                f"Duplicate item definition: {identifier}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
            continue
        seen[identifier] = item

        actual_kind = _kind_for_id(identifier)
        if kind != actual_kind:
            _add_issue(
                issues,
                "ID007",
                f"{identifier} is declared as {kind!r}, expected {actual_kind!r}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
        definition = inventory_by_id.get(identifier)
        if definition is None:
            _add_issue(
                issues,
                "ID008",
                f"Indexed item has no normative heading: {identifier}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
        else:
            defined_at = item.get("defined_at")
            raw_path = defined_at.get("path") if isinstance(defined_at, dict) else None
            indexed_path = _safe_repo_path(
                root,
                raw_path,
                issues,
                code="ID009",
                context=f"items[{offset}].defined_at.path",
            )
            if indexed_path is not None and _relative(indexed_path, root) != definition.path:
                _add_issue(
                    issues,
                    "ID010",
                    f"{identifier} points to {_relative(indexed_path, root)}, "
                    f"but its heading is in {definition.path}.",
                    path=INDEX_RELATIVE_PATH.as_posix(),
                )

    missing = sorted(set(inventory_by_id) - set(seen))
    if missing:
        _add_issue(
            issues,
            "ID011",
            "Normative headings missing from items: " + ", ".join(missing),
            path=INDEX_RELATIVE_PATH.as_posix(),
        )

    for kind in active:
        active[kind] = {
            identifier
            for identifier in active[kind]
            if identifier in seen
            and _normalise_status(seen[identifier].get("status")) in ACTIVE_ITEM_STATUSES
        }
    return (
        active["requirement"],
        active["contract"],
        active["acceptance"],
        active["dataset"],
    )


def _validate_json_fences(
    root: Path,
    paths: Iterable[Path],
    issues: list[Issue],
) -> None:
    for path in paths:
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        for index, block in enumerate(JSON_FENCE.findall(_read(path)), start=1):
            try:
                strict_json_loads(block)
            except (json.JSONDecodeError, DuplicateKeyError) as exc:
                _add_issue(
                    issues,
                    "DOC001",
                    f"Invalid strict JSON example (block {index}): {exc}.",
                    path=_relative(path, root),
                )


def _validate_forbidden_phrases(paths: Iterable[Path], issues: list[Issue]) -> None:
    text = "\n".join(
        _read(path)
        for path in paths
        if path.exists() and path.suffix.lower() == ".md"
    ).lower()
    forbidden_phrases = {
        "component-free": "The normative package must not disable ontology components.",
        "componenti è disabilitata": "The normative package must not disable components.",
        "componenti sono disabilitati": "The normative package must not disable components.",
    }
    for phrase, message in forbidden_phrases.items():
        if phrase in text:
            _add_issue(issues, "DOC002", message)


def _ontology_path_and_hash(
    root: Path,
    index: dict[str, Any],
    issues: list[Issue],
) -> tuple[Path | None, str | None]:
    package = index.get("package")
    ontology = package.get("ontology") if isinstance(package, dict) else None
    if not isinstance(ontology, dict):
        _add_issue(
            issues,
            "ONT001",
            "package.ontology must be an object.",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )
        return None, None

    path = _safe_repo_path(
        root,
        ontology.get("path"),
        issues,
        code="ONT002",
        context="package.ontology.path",
    )
    expected = ontology.get("sha256")
    if not isinstance(expected, str):
        _add_issue(
            issues,
            "ONT003",
            "package.ontology.sha256 must be a SHA-256 string.",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )
        expected_hash = None
    else:
        expected_hash = expected.removeprefix("sha256:").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            _add_issue(
                issues,
                "ONT004",
                f"Invalid ontology checksum: {expected!r}.",
                path=INDEX_RELATIVE_PATH.as_posix(),
            )
            expected_hash = None

    if path is None:
        return None, expected_hash
    if not path.exists():
        _add_issue(issues, "ONT005", "Ontology file does not exist.", path=_relative(path, root))
        return path, expected_hash

    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_hash is not None and actual != expected_hash:
        _add_issue(
            issues,
            "ONT006",
            f"Ontology checksum mismatch: expected {expected_hash}, got {actual}.",
            path=_relative(path, root),
        )
    return path, actual


def _canonical_index_for_digest(index: dict[str, Any]) -> dict[str, Any]:
    canonical = copy.deepcopy(index)
    canonical.pop("readiness", None)
    package = canonical.get("package")
    if isinstance(package, dict):
        package.pop("snapshot_sha256", None)
        package.pop("digest", None)
    return canonical


def compute_package_digest(
    root: Path | str,
    index: dict[str, Any],
    normative_paths: Iterable[Path] | None = None,
    ontology_path: Path | None = None,
) -> str:
    """Compute the approval digest without self-referential readiness fields."""

    root_path = Path(root).resolve()
    if normative_paths is None:
        documents = index.get("package", {}).get("normative_documents", [])
        resolved: list[Path] = []
        for document in documents:
            raw_path = document.get("path") if isinstance(document, dict) else document
            if isinstance(raw_path, str) and not Path(raw_path).is_absolute():
                candidate = (root_path / raw_path).resolve()
                if candidate.is_relative_to(root_path) and candidate.exists():
                    resolved.append(candidate)
        normative_paths = resolved

    if ontology_path is None:
        ontology = index.get("package", {}).get("ontology", {})
        raw_ontology_path = ontology.get("path") if isinstance(ontology, dict) else None
        if isinstance(raw_ontology_path, str) and not Path(raw_ontology_path).is_absolute():
            candidate = (root_path / raw_ontology_path).resolve()
            if candidate.is_relative_to(root_path) and candidate.exists():
                ontology_path = candidate

    digest = hashlib.sha256()
    canonical = json.dumps(
        _canonical_index_for_digest(index),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest.update(b"SPEC_INDEX\0")
    digest.update(canonical)

    selected_paths = {
        path.resolve()
        for path in normative_paths
        if path.exists() and path.name != "SPEC_READINESS_REPORT.md"
    }
    schema_path = (root_path / SCHEMA_RELATIVE_PATH).resolve()
    if schema_path.exists():
        selected_paths.add(schema_path)
    if ontology_path is not None and ontology_path.exists():
        selected_paths.add(ontology_path.resolve())

    for path in sorted(selected_paths, key=lambda candidate: _relative(candidate, root_path)):
        digest.update(b"\0FILE\0")
        digest.update(_relative(path, root_path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _validate_verifications(
    root: Path,
    records: dict[str, dict[str, Any]],
    dataset_ids: set[str],
    issues: list[Issue],
) -> set[str]:
    used_datasets: set[str] = set()
    for identifier, record in records.items():
        kind = str(record.get("kind") or "").lower()
        lifecycle = str(record.get("lifecycle") or "").lower()
        assertion = record.get("assertion")
        if kind not in {"automated", "manual"}:
            _add_issue(issues, "VER001", f"{identifier} has invalid kind {kind!r}.")
        if lifecycle not in {"specified", "implemented"}:
            _add_issue(issues, "VER002", f"{identifier} has invalid lifecycle {lifecycle!r}.")
        if _is_placeholder(assertion):
            _add_issue(issues, "VER003", f"{identifier} must declare a substantive assertion.")

        target = record.get("target")
        protocol = record.get("protocol")
        if kind == "automated" and _is_placeholder(target):
            _add_issue(issues, "VER004", f"Automated verification {identifier} requires target.")
        if kind == "manual" and _is_placeholder(target) and _is_placeholder(protocol):
            _add_issue(
                issues,
                "VER005",
                f"Manual verification {identifier} requires target or protocol.",
            )

        if lifecycle == "implemented" and isinstance(target, str):
            file_part = target.split("::", 1)[0].split("#", 1)[0]
            if file_part and ("/" in file_part or Path(file_part).suffix):
                target_path = _safe_repo_path(
                    root,
                    file_part,
                    issues,
                    code="VER006",
                    context=f"{identifier}.target",
                )
                if target_path is not None and not target_path.exists():
                    _add_issue(
                        issues,
                        "VER007",
                        f"Implemented verification target does not exist: {file_part}.",
                    )

        raw_dataset_ids = record.get("dataset_ids", [])
        if not isinstance(raw_dataset_ids, list):
            _add_issue(issues, "VER008", f"{identifier}.dataset_ids must be an array.")
            continue
        if len(raw_dataset_ids) != len(set(raw_dataset_ids)):
            _add_issue(issues, "VER009", f"{identifier} has duplicate dataset references.")
        for dataset_id in raw_dataset_ids:
            if dataset_id not in dataset_ids:
                _add_issue(
                    issues,
                    "VER010",
                    f"{identifier} references unknown dataset {dataset_id!r}.",
                )
            else:
                used_datasets.add(dataset_id)
    return used_datasets


def _validate_artifacts(
    records: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> None:
    observable_fields = ("path", "path_pattern", "schema_ref", "observables")
    for identifier, record in records.items():
        lifecycle = str(record.get("lifecycle") or "").lower()
        if lifecycle not in {"specified", "implemented"}:
            _add_issue(issues, "ART001", f"{identifier} has invalid lifecycle {lifecycle!r}.")
        if not any(record.get(field) for field in observable_fields):
            _add_issue(
                issues,
                "ART002",
                f"{identifier} must expose a path, pattern, schema, or observable selector.",
            )


def _validate_obligations(
    records: dict[str, dict[str, Any]],
    *,
    source_ids: set[str],
    acceptance_ids: set[str],
    verification_ids: set[str],
    artifact_ids: set[str],
    issues: list[Issue],
) -> tuple[set[str], set[str], set[str], set[str]]:
    covered_sources: set[str] = set()
    used_acceptance: set[str] = set()
    used_verifications: set[str] = set()
    used_artifacts: set[str] = set()

    for identifier, record in records.items():
        source_id = record.get("source_id")
        if source_id not in source_ids:
            _add_issue(
                issues,
                "TRC001",
                f"{identifier} references unknown or inactive requirement/contract {source_id!r}.",
            )
        else:
            covered_sources.add(source_id)

        if _is_placeholder(record.get("verified_behavior")):
            _add_issue(
                issues,
                "TRC002",
                f"{identifier} must declare the behavior its evidence verifies.",
            )

        reference_groups = (
            ("acceptance_ids", acceptance_ids, used_acceptance, "acceptance", "TRC003"),
            (
                "verification_ids",
                verification_ids,
                used_verifications,
                "verification",
                "TRC004",
            ),
            ("artifact_ids", artifact_ids, used_artifacts, "artifact", "TRC005"),
        )
        for field, known, used, label, code in reference_groups:
            values = record.get(field)
            if not isinstance(values, list) or not values:
                _add_issue(issues, code, f"{identifier}.{field} must be a non-empty array.")
                continue
            if len(values) != len(set(values)):
                _add_issue(issues, "TRC006", f"{identifier}.{field} contains duplicates.")
            for value in values:
                if value not in known:
                    _add_issue(
                        issues,
                        code,
                        f"{identifier} references unknown {label} {value!r}.",
                    )
                else:
                    used.add(value)

    uncovered = sorted(source_ids - covered_sources)
    if uncovered:
        _add_issue(
            issues,
            "TRC007",
            "Requirements/contracts without an obligation: " + ", ".join(uncovered),
        )
    orphan_acceptance = sorted(acceptance_ids - used_acceptance)
    if orphan_acceptance:
        _add_issue(
            issues,
            "TRC008",
            "Acceptance criteria not used by any obligation: " + ", ".join(orphan_acceptance),
        )
    orphan_verifications = sorted(verification_ids - used_verifications)
    if orphan_verifications:
        _add_issue(
            issues,
            "TRC009",
            "Verifications not used by any obligation: " + ", ".join(orphan_verifications),
        )
    orphan_artifacts = sorted(artifact_ids - used_artifacts)
    if orphan_artifacts:
        _add_issue(
            issues,
            "TRC010",
            "Artifacts not used by any obligation: " + ", ".join(orphan_artifacts),
        )
    return covered_sources, used_acceptance, used_verifications, used_artifacts


def _validate_decisions(
    records: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> list[str]:
    blockers: list[str] = []
    for identifier, record in records.items():
        status = _normalise_status(record.get("status"))
        scope = str(record.get("scope") or "").lower()
        planning_blocker = record.get("planning_blocker") is True
        if status not in {
            "OPEN",
            "PROPOSED",
            "ACCEPTED",
            "REJECTED",
            "SUPERSEDED",
            "DEFERRED",
        }:
            _add_issue(issues, "DEC001", f"{identifier} has invalid status {status!r}.")
        if scope not in {"product", "implementation"}:
            _add_issue(issues, "DEC002", f"{identifier} has invalid scope {scope!r}.")
        if _is_placeholder(record.get("statement")):
            _add_issue(issues, "DEC003", f"{identifier} must declare a substantive statement.")

        unresolved = status not in TERMINAL_DECISION_STATUSES
        if unresolved and (planning_blocker or scope == "product"):
            blockers.append(f"Blocking decision remains {status or 'UNSPECIFIED'}: {identifier}")
            _add_issue(
                issues,
                "DEC004",
                blockers[-1],
                category="readiness",
            )
        if status == "DEFERRED" and scope == "product":
            _add_issue(
                issues,
                "DEC005",
                f"Product decision {identifier} cannot be deferred to implementation.",
                category="readiness",
            )
        if status == "SUPERSEDED":
            replacement = record.get("superseded_by")
            if replacement not in records or replacement == identifier:
                _add_issue(
                    issues,
                    "DEC006",
                    f"{identifier} must reference a different known decision in superseded_by.",
                )

    for identifier in records:
        visited: set[str] = set()
        current = identifier
        while current in records and _normalise_status(records[current].get("status")) == "SUPERSEDED":
            if current in visited:
                _add_issue(
                    issues,
                    "DEC007",
                    f"Decision supersession cycle includes {identifier}.",
                )
                break
            visited.add(current)
            replacement = records[current].get("superseded_by")
            if not isinstance(replacement, str):
                break
            current = replacement
    return blockers


def _validate_findings(
    records: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> list[str]:
    blockers: list[str] = []
    for identifier, record in records.items():
        status = _normalise_status(record.get("status"))
        planning_blocker = record.get("planning_blocker") is True
        disposition = str(record.get("planning_disposition") or "").lower()
        if status not in {"OPEN", "RESOLVED", "CLOSED", "ACCEPTED_RISK", "DEFERRED"}:
            _add_issue(issues, "AUD001", f"{identifier} has invalid status {status!r}.")
        if _is_placeholder(record.get("summary")):
            _add_issue(issues, "AUD002", f"{identifier} must declare a substantive summary.")

        must_resolve = planning_blocker or disposition == "must_resolve_pre_plan"
        if must_resolve and status not in TERMINAL_FINDING_STATUSES:
            blockers.append(f"Blocking audit finding remains {status or 'UNSPECIFIED'}: {identifier}")
            _add_issue(
                issues,
                "AUD003",
                blockers[-1],
                category="readiness",
            )
        if status in TERMINAL_FINDING_STATUSES:
            references = record.get("resolution_refs")
            if not isinstance(references, list) or not references:
                _add_issue(
                    issues,
                    "AUD004",
                    f"Resolved finding {identifier} requires resolution_refs.",
                )
    return blockers


def _validate_cross_references(
    decisions: dict[str, dict[str, Any]],
    findings: dict[str, dict[str, Any]],
    known_ids: set[str],
    issues: list[Issue],
) -> None:
    for registry_name, records in (("decision", decisions), ("finding", findings)):
        for identifier, record in records.items():
            for field in ("related_ids", "resolution_refs"):
                values = record.get(field, [])
                if not isinstance(values, list):
                    _add_issue(
                        issues,
                        "REF001",
                        f"{identifier}.{field} must be an array.",
                    )
                    continue
                for value in values:
                    if value not in known_ids:
                        _add_issue(
                            issues,
                            "REF002",
                            f"{registry_name} {identifier} references unknown ID {value!r} in {field}.",
                        )


def _validate_decision_register(
    root: Path,
    decisions: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> None:
    path = root / "docs/specs/DECISION_REGISTER.md"
    if not path.exists():
        return
    rows = DECISION_ROW.findall(_read(path))
    if not rows:
        return
    row_ids = [identifier for identifier, _ in rows]
    duplicates = sorted(
        identifier for identifier, count in Counter(row_ids).items() if count > 1
    )
    if duplicates:
        _add_issue(
            issues,
            "DEC008",
            "Duplicate decisions in Markdown register: " + ", ".join(duplicates),
            path=_relative(path, root),
        )
    row_statuses = {identifier: status for identifier, status in rows}
    missing = sorted(set(decisions) - set(row_statuses))
    unknown = sorted(set(row_statuses) - set(decisions))
    if missing:
        _add_issue(
            issues,
            "DEC009",
            "Indexed decisions missing from Markdown register: " + ", ".join(missing),
            path=_relative(path, root),
        )
    if unknown:
        _add_issue(
            issues,
            "DEC010",
            "Markdown decisions missing from specification index: " + ", ".join(unknown),
            path=_relative(path, root),
        )
    for identifier in sorted(set(decisions) & set(row_statuses)):
        expected = _normalise_status(decisions[identifier].get("status"))
        actual = _normalise_status(row_statuses[identifier])
        if expected != actual:
            _add_issue(
                issues,
                "DEC011",
                f"{identifier} status mismatch: index={expected}, Markdown={actual}.",
                path=_relative(path, root),
            )


def _approval_status(
    record: Any,
    *,
    label: str,
    digest: str,
    issues: list[Issue],
) -> str:
    if not isinstance(record, dict):
        _add_issue(issues, "RDY001", f"{label} must be an object.")
        return ""
    status = _normalise_status(record.get("status"))
    if status not in {"PENDING", "APPROVED", "REJECTED"}:
        _add_issue(issues, "RDY002", f"{label} has invalid status {status!r}.")
        return status
    if status != "APPROVED":
        return status

    valid = True
    identity_field = "reviewer" if label == "semantic_review" else "approver"
    if _is_placeholder(record.get(identity_field)):
        _add_issue(
            issues,
            "RDY003",
            f"Approved {label} requires {identity_field}.",
            category="readiness",
        )
        valid = False
    if _is_placeholder(record.get("approved_at")):
        _add_issue(
            issues,
            "RDY004",
            f"Approved {label} requires approved_at.",
            category="readiness",
        )
        valid = False
    approval_digest = record.get("package_digest")
    normalised_digest = (
        approval_digest.removeprefix("sha256:").lower()
        if isinstance(approval_digest, str)
        else None
    )
    if normalised_digest != digest:
        _add_issue(
            issues,
            "RDY005",
            f"{label} is stale or unbound: expected digest {digest}, got {approval_digest!r}.",
            category="readiness",
        )
        valid = False
    return status if valid else "INVALID"


def _derive_readiness(
    index: dict[str, Any],
    *,
    digest: str,
    pre_readiness_issues: list[Issue],
    decision_blockers: list[str],
    finding_blockers: list[str],
    issues: list[Issue],
) -> Readiness:
    readiness = index.get("readiness")
    if not isinstance(readiness, dict):
        return Readiness(None, "NOT_READY", digest, ("readiness object is invalid",))

    declared = readiness.get("declared_status")
    if declared not in READINESS_STATUSES:
        _add_issue(
            issues,
            "RDY006",
            f"Invalid declared readiness status: {declared!r}.",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )
        declared_value: str | None = None
    else:
        declared_value = declared

    package = index.get("package")
    snapshot = package.get("snapshot_sha256") if isinstance(package, dict) else None
    normalised_snapshot = (
        snapshot.removeprefix("sha256:").lower() if isinstance(snapshot, str) else None
    )
    if normalised_snapshot != digest:
        _add_issue(
            issues,
            "RDY007",
            f"package.snapshot_sha256 must match current digest {digest}; got {snapshot!r}.",
            category="readiness",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )

    semantic_status = _approval_status(
        readiness.get("semantic_review"),
        label="semantic_review",
        digest=digest,
        issues=issues,
    )
    owner_status = _approval_status(
        readiness.get("owner_approval"),
        label="owner_approval",
        digest=digest,
        issues=issues,
    )

    blockers = list(decision_blockers) + list(finding_blockers)
    blocking_codes = {
        issue.code
        for issue in pre_readiness_issues
        if issue.category in {"consistency", "readiness"}
    }
    if blocking_codes:
        blockers.append("Structural or traceability validation has errors")

    if (
        blockers
        or semantic_status != "APPROVED"
        or owner_status in {"REJECTED", "INVALID", ""}
        or normalised_snapshot != digest
    ):
        derived = "NOT_READY"
        if semantic_status != "APPROVED":
            blockers.append("Semantic traceability review is not approved")
    elif owner_status == "APPROVED":
        derived = "READY_FOR_PLANNING"
    else:
        derived = "AWAITING_OWNER_APPROVAL"
        blockers.append("Owner approval is pending")

    if declared_value is not None and declared_value != derived:
        _add_issue(
            issues,
            "RDY008",
            f"Declared readiness {declared_value} does not match derived readiness {derived}.",
            category="readiness",
            path=INDEX_RELATIVE_PATH.as_posix(),
        )
    if derived == "AWAITING_OWNER_APPROVAL":
        _add_issue(
            issues,
            "RDY009",
            "Specification package awaits owner approval.",
            category="readiness",
        )
    elif derived == "NOT_READY" and not blockers:
        blockers.append("Specification package has unresolved readiness errors")

    return Readiness(
        declared_status=declared_value,
        derived_status=derived,
        package_digest=digest,
        blockers=tuple(dict.fromkeys(blockers)),
    )


def _evaluate_index(root: Path, index: dict[str, Any], issues: list[Issue]) -> Evaluation:
    _validate_schema(root, index, issues)
    normative_paths = _normative_document_paths(root, index, issues)
    inventory = _extract_inventory(root, normative_paths, issues)
    requirement_ids, contract_ids, acceptance_ids, dataset_ids = _validate_items(
        root,
        index,
        inventory,
        issues,
    )

    _validate_json_fences(root, normative_paths, issues)
    _validate_forbidden_phrases(normative_paths, issues)
    ontology_path, _ = _ontology_path_and_hash(root, index, issues)

    obligations = _registry(
        _records(index, "obligations", issues),
        kind="obligation",
        issues=issues,
    )
    verifications = _registry(
        _records(index, "verifications", issues),
        kind="verification",
        issues=issues,
    )
    artifacts = _registry(
        _records(index, "artifacts", issues),
        kind="artifact",
        issues=issues,
    )
    decisions = _registry(
        _records(index, "decisions", issues),
        kind="decision",
        issues=issues,
    )
    findings = _registry(
        _records(index, "findings", issues),
        kind="finding",
        issues=issues,
    )

    global_ids: dict[str, str] = {}
    registries = (
        ("normative", {definition.identifier: {} for definition in inventory.definitions}),
        ("obligation", obligations),
        ("verification", verifications),
        ("artifact", artifacts),
        ("decision", decisions),
        ("finding", findings),
    )
    for namespace, records in registries:
        for identifier in records:
            previous = global_ids.get(identifier)
            if previous is not None and previous != namespace:
                _add_issue(
                    issues,
                    "ID012",
                    f"ID {identifier} is reused across {previous} and {namespace}.",
                )
            global_ids[identifier] = namespace

    used_datasets = _validate_verifications(root, verifications, dataset_ids, issues)
    _validate_artifacts(artifacts, issues)
    _validate_obligations(
        obligations,
        source_ids=requirement_ids | contract_ids,
        acceptance_ids=acceptance_ids,
        verification_ids=set(verifications),
        artifact_ids=set(artifacts),
        issues=issues,
    )
    unused_datasets = sorted(dataset_ids - used_datasets)
    if unused_datasets:
        _add_issue(
            issues,
            "TRC011",
            "Datasets not used by any verification: " + ", ".join(unused_datasets),
        )

    decision_blockers = _validate_decisions(decisions, issues)
    finding_blockers = _validate_findings(findings, issues)
    known_ids = (
        set(global_ids)
        | requirement_ids
        | contract_ids
        | acceptance_ids
        | dataset_ids
    )
    _validate_cross_references(decisions, findings, known_ids, issues)
    _validate_decision_register(root, decisions, issues)

    digest = compute_package_digest(
        root,
        index,
        normative_paths=normative_paths,
        ontology_path=ontology_path,
    )
    pre_readiness_issues = list(issues)
    readiness = _derive_readiness(
        index,
        digest=digest,
        pre_readiness_issues=pre_readiness_issues,
        decision_blockers=decision_blockers,
        finding_blockers=finding_blockers,
        issues=issues,
    )
    return Evaluation(tuple(issues), inventory, readiness, index_present=True)


def _evaluate_without_index(root: Path, issues: list[Issue]) -> Evaluation:
    paths = [root / relative for relative in DEFAULT_NORMATIVE_DOCUMENTS]
    for path in paths:
        if not path.exists():
            _add_issue(issues, "LEG001", "Required normative file is missing.", path=_relative(path, root))
    inventory = _extract_inventory(root, paths, issues)

    matrix_path = root / "docs/specs/TRACEABILITY_MATRIX.md"
    if matrix_path.exists():
        matrix_text = _read(matrix_path)
        requirement_refs = set(REQUIREMENT_REFERENCE.findall(matrix_text))
        acceptance_refs = set(ACCEPTANCE_REFERENCE.findall(matrix_text))
        requirements = inventory.ids("requirement")
        acceptance = inventory.ids("acceptance")
        if requirements - requirement_refs:
            _add_issue(
                issues,
                "LEG002",
                "Requirements missing from traceability matrix: "
                + ", ".join(sorted(requirements - requirement_refs)),
            )
        if requirement_refs - requirements:
            _add_issue(
                issues,
                "LEG003",
                "Unknown requirement references in matrix: "
                + ", ".join(sorted(requirement_refs - requirements)),
            )
        if acceptance - acceptance_refs:
            _add_issue(
                issues,
                "LEG004",
                "Acceptance criteria missing from traceability matrix: "
                + ", ".join(sorted(acceptance - acceptance_refs)),
            )
        if acceptance_refs - acceptance:
            _add_issue(
                issues,
                "LEG005",
                "Unknown acceptance references in matrix: "
                + ", ".join(sorted(acceptance_refs - acceptance)),
            )

    ontology_path = root / "ontology_schema.JSON"
    if ontology_path.exists():
        actual = hashlib.sha256(ontology_path.read_bytes()).hexdigest()
        if actual != EXPECTED_ONTOLOGY_SHA256:
            _add_issue(
                issues,
                "LEG006",
                f"Ontology checksum mismatch: expected {EXPECTED_ONTOLOGY_SHA256}, got {actual}.",
                path=_relative(ontology_path, root),
            )
    else:
        _add_issue(issues, "LEG007", "Ontology file is missing.", path="ontology_schema.JSON")
    _validate_json_fences(root, paths, issues)
    _validate_forbidden_phrases(paths, issues)
    readiness = Readiness(
        declared_status=None,
        derived_status="NOT_READY",
        package_digest=None,
        blockers=("SPEC_INDEX.json is missing",),
    )
    return Evaluation(tuple(issues), inventory, readiness, index_present=False)


def evaluate(root: Path | str = ROOT) -> Evaluation:
    """Return structured consistency and readiness results for a repository root."""

    root_path = Path(root).resolve()
    issues: list[Issue] = []
    index = _load_index(root_path, issues)
    if index is None:
        return _evaluate_without_index(root_path, issues)
    return _evaluate_index(root_path, index, issues)


def validate(root: Path | str = ROOT) -> list[str]:
    """Backward-compatible validation API returning rendered error strings."""

    return evaluate(root).messages()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to validate.")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--require-status",
        choices=sorted(READINESS_STATUSES),
        help="Fail unless the derived readiness has this exact status.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = evaluate(args.root)
    status_mismatch = (
        args.require_status is not None
        and result.readiness.derived_status != args.require_status
    )

    if args.format == "json":
        payload = result.as_dict()
        if args.require_status is not None:
            payload["required_status"] = args.require_status
            payload["required_status_satisfied"] = not status_mismatch
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if result.issues:
            for issue in result.issues:
                print(f"ERROR: {issue.render()}")
        else:
            counts = result.inventory.counts()
            print(
                "Specification package is consistent: "
                f"{counts['requirement']} requirements, "
                f"{counts['contract']} contracts, "
                f"{counts['acceptance']} acceptance criteria, "
                f"{counts['dataset']} datasets."
            )
        print(
            "Planning readiness: "
            f"{result.readiness.derived_status} "
            f"(digest {result.readiness.package_digest or 'unavailable'})."
        )
        if status_mismatch:
            print(
                "ERROR: "
                f"required readiness {args.require_status}, "
                f"got {result.readiness.derived_status}."
            )

    return 1 if result.issues or status_mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
