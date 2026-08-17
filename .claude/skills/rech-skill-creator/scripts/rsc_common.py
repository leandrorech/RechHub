"""rsc_common.py - shared utilities for rech-skill-creator scripts.

Single source of truth for:
  - YAML parsing (PyYAML safe_load only - see defect #10; no other module in
    this skill is permitted to hand-parse or pre-process YAML/JSON text)
  - Canonicalization (stable, whitespace/comment-insensitive re-serialization)
  - SHA-256 hashing of files, directories and canonicalized YAML/JSON
  - Small shared dataclasses/enums reused across every gate script, so the
    verdict vocabulary of each gate lives in exactly one place.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

# ---------------------------------------------------------------------------
# YAML / JSON I/O
# ---------------------------------------------------------------------------


def load_yaml(path: "str | Path") -> Any:
    """Parse a YAML file via PyYAML's safe_load exclusively.

    This is the ONLY YAML-parsing code path in the whole skill (defect #10:
    a prior validator that hand-scanned lines for `key: value` misread text
    inside block scalars — e.g. a line containing ':' inside a `|` literal —
    as new top-level structure). No caller may pre-process file text by line
    before or after this call; every script imports load_yaml() instead of
    touching yaml.safe_load() directly, so there is exactly one parsing
    implementation to keep correct.
    """
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_yaml_str(text: str) -> Any:
    return yaml.safe_load(text)


def canonical_yaml_bytes(data: Any) -> bytes:
    """Deterministic re-serialization: stable key order, no comment/whitespace
    noise, so a purely cosmetic edit never changes the resulting hash while
    any real value change always does."""
    return yaml.safe_dump(
        data, sort_keys=True, default_flow_style=False, allow_unicode=True
    ).encode("utf-8")


def canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file_raw(path: "str | Path") -> str:
    with open(path, "rb") as fh:
        return sha256_bytes(fh.read())


def sha256_yaml_canonical(path: "str | Path") -> str:
    return sha256_bytes(canonical_yaml_bytes(load_yaml(path)))


def sha256_json_canonical(path: "str | Path") -> str:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return sha256_bytes(canonical_json_bytes(data))


IGNORED_DIR_NAMES = {".git", "__pycache__", "snapshot", ".pytest_cache", "node_modules"}


def hash_directory(root: "str | Path") -> str:
    """Merkle-lite tree hash: a sorted list of 'relpath:sha256(file bytes)'
    lines, joined with '\\n' and hashed as a whole.

    Deliberately NOT a tarball/archive hash: tar embeds mtime/uid/permission
    bits, which would make a fresh checkout with byte-identical file content
    register as a false-positive integrity failure. Only file paths and byte
    content participate in the hash.
    """
    root = Path(root)
    lines: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIR_NAMES)
        for fn in sorted(filenames):
            fpath = Path(dirpath) / fn
            relpath = fpath.relative_to(root).as_posix()
            lines.append(f"{relpath}:{sha256_file_raw(fpath)}")
    lines.sort()
    return sha256_bytes("\n".join(lines).encode("utf-8"))


def hash_path_smart(path: Optional["str | Path"]) -> tuple[str, Optional[str]]:
    """Return (kind, sha256) for a declared decision-input path.

    kind is one of 'none' | 'file' | 'directory'. A path that is None or does
    not exist on disk is reported as ('none', None) — an explicit, hashed
    declaration of absence (used for ORIGINAL/PREVIOUS on a brand-new skill
    with no history), never silently omitted from the decision-input manifest.
    YAML/JSON files are canonicalized before hashing; every other file is
    hashed as raw bytes; directories use hash_directory().
    """
    if path is None:
        return "none", None
    p = Path(path)
    if not p.exists():
        return "none", None
    if p.is_dir():
        return "directory", hash_directory(p)
    suffix = p.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return "file", sha256_yaml_canonical(p)
    if suffix == ".json":
        return "file", sha256_json_canonical(p)
    return "file", sha256_file_raw(p)


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------


class RunOutcome(str, Enum):
    """Outcome of a single declared eval inside a single run directory.

    RUN_INVALID (timeout / infra exception) is a THIRD bucket, distinct from
    both PASS and FAIL — it must never be counted as a functional pass, and
    must never be counted as a functional failure either; it simply removes
    the run from consideration (see valid_run_gate.py)."""

    PASS = "PASS"
    FAIL = "FAIL"
    RUN_INVALID = "RUN_INVALID"


class GateVerdict(str, Enum):
    """Binary verdict for VALID_RUN_GATE and ARTIFACT_INTEGRITY_GATE."""

    PASS = "PASS"
    FAIL = "FAIL"


class IsolationStatus(str, Enum):
    """EVAL_ISOLATION status family. PASS is reachable only with an explicit,
    complete, overlap-free --scope. Missing scope -> UNVERIFIED (never PASS).
    Insufficient/overlapping scope -> PARTIAL (never PASS)."""

    PASS = "PASS"
    PARTIAL = "PARTIAL"
    UNVERIFIED = "UNVERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ReleaseVerdict(str, Enum):
    """PACKAGE_RELEASE_GATE verdict. RELEASABLE (not READY) is a deliberate
    lexical choice, distinct from the unrelated sibling skill rech-release-gate
    (which decides RECH *product* release readiness, not skill-package
    packaging) - on top of the internal function/module naming fix."""

    RELEASABLE = "RELEASABLE"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


class CheckStatus(str, Enum):
    """Per-check status used by skills_api_validate.py and package_validate.py.
    NOT_APPLICABLE is reserved for checks that cannot be performed at all in
    this environment (e.g. live network calls) - it is never a synonym for
    PASS and must always be listed explicitly, never omitted."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNVERIFIED = "UNVERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Shared result container
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    gate: str
    verdict: str
    reason: str
    evidence: list = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "verdict": self.verdict,
            "reason": self.reason,
            "evidence": self.evidence,
            "details": self.details,
        }

    @property
    def ok(self) -> bool:
        return self.verdict in ("PASS", "RELEASABLE")


# ---------------------------------------------------------------------------
# Misc small helpers
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: "str | Path", obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def read_json(path: "str | Path") -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def discover_run_dirs(runs_dir: "str | Path") -> list:
    """Only real directories that exist on disk are returned - the normalizer
    must never synthesize a fake run-N/ just to 'complete' a benchmark."""
    runs_dir = Path(runs_dir)
    if not runs_dir.exists():
        return []
    return sorted(
        (p for p in runs_dir.iterdir() if p.is_dir() and p.name.startswith("run-")),
        key=lambda p: p.name,
    )
