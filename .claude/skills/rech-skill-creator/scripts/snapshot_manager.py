#!/usr/bin/env python3
"""snapshot_manager.py - freezes and hashes EVAL_MANIFEST and every other
decision input BEFORE any run may execute (fixes defects #1 and #8, which are
the same requirement stated twice in the source material).

Two artifacts are written under `<workdir>/snapshot/`:

  eval_manifest.canonical.yaml
      A canonicalized COPY of the eval manifest. Every downstream stage
      (run_executor.py, valid_run_gate.py) is only permitted to read this
      frozen copy, never the live working file — this is what structurally
      guarantees a run cannot see a manifest that was not snapshotted first.

  decision_input_manifest.json
      One entry per decision-input category (ORIGINAL, PREVIOUS, CANDIDATE,
      EVAL_MANIFEST, CONTRACT, EVAL_DEFINITIONS_FIXTURES, CONFIG), each with
      its kind ('none'|'file'|'directory') and SHA-256. artifact_integrity_gate.py
      recomputes every one of these on demand and compares against this frozen
      record (defect #3: ALL inputs are protected uniformly, not just CANDIDATE).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import (  # noqa: E402
    canonical_yaml_bytes,
    hash_path_smart,
    load_yaml,
    now_iso,
    sha256_bytes,
    canonical_json_bytes,
    write_json,
)

SNAPSHOT_DIRNAME = "snapshot"
CANONICAL_MANIFEST_NAME = "eval_manifest.canonical.yaml"
DECISION_INPUT_MANIFEST_NAME = "decision_input_manifest.json"


def _eval_assertions_digest(eval_entry: dict) -> str:
    assertions = eval_entry.get("assertions", [])
    return sha256_bytes(canonical_yaml_bytes(assertions))


def freeze(
    workdir: "str | Path",
    eval_manifest: Optional["str | Path"] = None,
    contract: Optional["str | Path"] = None,
    original: Optional["str | Path"] = None,
    previous: Optional["str | Path"] = None,
    candidate: Optional["str | Path"] = None,
    eval_fixtures: Optional[list] = None,
    config: Optional["str | Path"] = None,
) -> dict:
    """Freeze the eval manifest and every decision input under
    `<workdir>/snapshot/`. Returns the decision_input_manifest dict that was
    written. Idempotent: re-freezing overwrites the prior snapshot — callers
    that want mutation-detection semantics should freeze once and rely on
    artifact_integrity_gate.py to detect later changes, not re-freeze to
    "launder" a changed input.
    """
    workdir = Path(workdir)
    eval_manifest = Path(eval_manifest) if eval_manifest else workdir / "eval_manifest.yaml"
    contract = Path(contract) if contract else workdir / "contract.yaml"
    candidate = Path(candidate) if candidate else workdir
    eval_fixtures = [Path(p) for p in (eval_fixtures or [])]

    if not eval_manifest.exists():
        raise FileNotFoundError(f"EVAL_MANIFEST not found: {eval_manifest}")

    manifest_data = load_yaml(eval_manifest)
    canonical_bytes = canonical_yaml_bytes(manifest_data)
    manifest_sha256 = sha256_bytes(canonical_bytes)

    snapshot_dir = workdir / SNAPSHOT_DIRNAME
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    canonical_path = snapshot_dir / CANONICAL_MANIFEST_NAME
    canonical_path.write_bytes(canonical_bytes)

    eval_assertion_digests = {
        e["eval_id"]: _eval_assertions_digest(e) for e in manifest_data.get("evals", [])
    }

    def _input_entry(path: Optional["str | Path"]) -> dict:
        kind, digest = hash_path_smart(path)
        return {"path": str(path) if path is not None else None, "kind": kind, "sha256": digest}

    inputs: dict = {
        "ORIGINAL": _input_entry(original),
        "PREVIOUS": _input_entry(previous),
        "CANDIDATE": _input_entry(candidate),
        "EVAL_MANIFEST": _input_entry(eval_manifest),
        "CONTRACT": _input_entry(contract) if contract.exists() else {
            "path": str(contract), "kind": "none", "sha256": None
        },
        "EVAL_DEFINITIONS_FIXTURES": [
            {"path": str(p), **dict(zip(("kind", "sha256"), hash_path_smart(p)))}
            for p in eval_fixtures
        ],
        "CONFIG": (
            {**_input_entry(config), "declared": True}
            if config is not None
            else {"path": None, "kind": "none", "sha256": None, "declared": False}
        ),
    }

    manifest_id = sha256_bytes(canonical_json_bytes(inputs))

    decision_input_manifest = {
        "manifest_id": manifest_id,
        "manifest_sha256": manifest_sha256,
        "created_at": now_iso(),
        "inputs": inputs,
        "eval_assertion_digests": eval_assertion_digests,
    }

    write_json(snapshot_dir / DECISION_INPUT_MANIFEST_NAME, decision_input_manifest)
    return decision_input_manifest


def is_frozen(workdir: "str | Path") -> bool:
    workdir = Path(workdir)
    return (workdir / SNAPSHOT_DIRNAME / CANONICAL_MANIFEST_NAME).exists() and (
        workdir / SNAPSHOT_DIRNAME / DECISION_INPUT_MANIFEST_NAME
    ).exists()


def canonical_manifest_path(workdir: "str | Path") -> Path:
    return Path(workdir) / SNAPSHOT_DIRNAME / CANONICAL_MANIFEST_NAME


def decision_input_manifest_path(workdir: "str | Path") -> Path:
    return Path(workdir) / SNAPSHOT_DIRNAME / DECISION_INPUT_MANIFEST_NAME


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    freeze_p = sub.add_parser("freeze", help="Freeze EVAL_MANIFEST and all decision inputs.")
    freeze_p.add_argument("--workdir", required=True)
    freeze_p.add_argument("--eval-manifest")
    freeze_p.add_argument("--contract")
    freeze_p.add_argument("--original")
    freeze_p.add_argument("--previous")
    freeze_p.add_argument("--candidate")
    freeze_p.add_argument("--eval-fixtures", nargs="*", default=[])
    freeze_p.add_argument("--config")

    args = parser.parse_args(argv)

    if args.command == "freeze":
        try:
            result = freeze(
                workdir=args.workdir,
                eval_manifest=args.eval_manifest,
                contract=args.contract,
                original=args.original,
                previous=args.previous,
                candidate=args.candidate,
                eval_fixtures=args.eval_fixtures,
                config=args.config,
            )
        except FileNotFoundError as exc:
            print(f"FREEZE FAILED: {exc}", file=sys.stderr)
            return 1
        print(f"FROZEN manifest_id={result['manifest_id']}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
