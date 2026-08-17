#!/usr/bin/env python3
"""artifact_integrity_gate.py - protects ALL decision inputs, not just
CANDIDATE (defect #3).

Recomputes the hash of every category recorded in
`<workdir>/snapshot/decision_input_manifest.json` (ORIGINAL, PREVIOUS,
CANDIDATE, EVAL_MANIFEST, CONTRACT, EVAL_DEFINITIONS_FIXTURES, CONFIG) using
the identical hashing function used at freeze time (rsc_common.hash_path_smart
- one implementation, imported, never re-derived here, so there is no drift
between what was frozen and what is re-checked). The SAME comparison loop
runs unconditionally over every category; there is no code path that treats
CANDIDATE differently from the rest.

PASS iff: a snapshot exists, every recorded input's recomputed hash matches
the stored hash, and nothing recorded as present is now missing. Any other
condition is FAIL, always reported with the itemized CHANGED/MISSING list as
evidence - never a bare boolean.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import GateResult, hash_path_smart, read_json  # noqa: E402
from snapshot_manager import decision_input_manifest_path  # noqa: E402

GATE_NAME = "ARTIFACT_INTEGRITY_GATE"

SCALAR_CATEGORIES = ("ORIGINAL", "PREVIOUS", "CANDIDATE", "EVAL_MANIFEST", "CONTRACT", "CONFIG")


def _check_scalar_entry(category: str, entry: dict) -> dict | None:
    """Recompute one scalar (non-list) decision-input entry. Returns a
    change/missing report dict, or None if it matches the stored record."""
    stored_kind = entry.get("kind")
    stored_hash = entry.get("sha256")
    path = entry.get("path")
    cur_kind, cur_hash = hash_path_smart(path)

    if stored_kind != "none" and cur_kind == "none":
        return {"category": category, "path": path, "status": "MISSING", "was": stored_hash}
    if cur_hash != stored_hash:
        return {"category": category, "path": path, "status": "CHANGED", "old": stored_hash, "new": cur_hash}
    return None


def _check_fixture_list(entries: list) -> list:
    reports = []
    for fixture in entries:
        stored_kind = fixture.get("kind")
        stored_hash = fixture.get("sha256")
        path = fixture.get("path")
        cur_kind, cur_hash = hash_path_smart(path)
        if stored_kind != "none" and cur_kind == "none":
            reports.append({"category": "EVAL_DEFINITIONS_FIXTURES", "path": path, "status": "MISSING", "was": stored_hash})
        elif cur_hash != stored_hash:
            reports.append({
                "category": "EVAL_DEFINITIONS_FIXTURES", "path": path, "status": "CHANGED",
                "old": stored_hash, "new": cur_hash,
            })
    return reports


def artifact_integrity_gate(workdir: "str | Path") -> GateResult:
    workdir = Path(workdir)
    manifest_path = decision_input_manifest_path(workdir)
    if not manifest_path.exists():
        return GateResult(gate=GATE_NAME, verdict="FAIL", reason="no snapshot found - run snapshot_manager.py freeze first")

    stored = read_json(manifest_path)
    inputs = stored.get("inputs", {})

    problems: list = []
    checked_categories: list = []

    # Uniform loop over every scalar category - no special case for CANDIDATE.
    for category in SCALAR_CATEGORIES:
        entry = inputs.get(category)
        checked_categories.append(category)
        if entry is None:
            problems.append({"category": category, "status": "MISSING_FROM_SNAPSHOT"})
            continue
        report = _check_scalar_entry(category, entry)
        if report:
            problems.append(report)

    checked_categories.append("EVAL_DEFINITIONS_FIXTURES")
    problems.extend(_check_fixture_list(inputs.get("EVAL_DEFINITIONS_FIXTURES", [])))

    if problems:
        changed = [p for p in problems if p.get("status") == "CHANGED"]
        missing = [p for p in problems if p.get("status") in ("MISSING", "MISSING_FROM_SNAPSHOT")]
        return GateResult(
            gate=GATE_NAME, verdict="FAIL",
            reason=f"{len(changed)} input(s) changed, {len(missing)} input(s) missing since snapshot",
            evidence=problems,
            details={"checked_categories": checked_categories, "manifest_id": stored.get("manifest_id")},
        )

    return GateResult(
        gate=GATE_NAME, verdict="PASS",
        reason="all decision inputs match the frozen snapshot",
        details={"checked_categories": checked_categories, "manifest_id": stored.get("manifest_id")},
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args(argv)

    result = artifact_integrity_gate(args.workdir)
    print(f"{result.gate}: {result.verdict} - {result.reason}")
    return 0 if result.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
