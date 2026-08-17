#!/usr/bin/env python3
"""valid_run_gate.py - PASS/FAIL over the actual run-N/ directories on disk,
checked against the FROZEN eval manifest (defect #2: a declared eval missing
from a run always FAILs the gate, it is never silently skipped or treated as
"not applicable").

Algorithm (see references/gate-semantics.md for the full prose walkthrough):

  1. Discover run-N/ directories on disk (never synthesized - an empty
     runs/ directory is simply zero runs, not padded to "complete" anything).
  2. For each run, first check STRUCTURAL completeness:
       a. run_meta.json must exist and its recorded manifest_sha256 must
          match the CURRENTLY frozen manifest's hash. A run executed against
          an older (since re-frozen) manifest is stale and cannot be used to
          satisfy this gate - it is reported as structurally incomplete, not
          silently accepted just because its eval outcomes happen to be
          present.
       b. every eval_id marked `required: true` in the frozen manifest must
          have a result.json under that run.
     Any run missing a required eval, or run against a stale manifest, fails
     the gate outright, before any outcome is even inspected.
  3. Among structurally-complete runs, a run is "valid" if none of its
     required evals came back RUN_INVALID. RUN_INVALID never counts as PASS
     and is never counted as a functional FAIL either - it just removes that
     run from the valid pool (a third bucket, see rsc_common.RunOutcome).
  4. If the number of valid runs is below `min_valid_runs` (default 1,
     configurable), the gate FAILs ("insufficient valid runs").
  5. Among valid runs, the gate PASSes only if every required eval in every
     valid run has outcome PASS.

Primary/baseline labels are read directly from the frozen manifest's explicit
`primary`/`baseline_ref` fields — this gate never infers them from directory
or list order.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import GateResult, discover_run_dirs, load_yaml, read_json  # noqa: E402
from snapshot_manager import canonical_manifest_path, decision_input_manifest_path, is_frozen  # noqa: E402

GATE_NAME = "VALID_RUN_GATE"


@dataclass
class RunEvaluation:
    run_id: str
    structurally_complete: bool
    missing_required: list = field(default_factory=list)
    stale_manifest: bool = False
    run_invalid_evals: list = field(default_factory=list)
    failed_evals: list = field(default_factory=list)
    is_valid: bool = False
    functional_pass: bool = False


def _evaluate_run(run_dir: Path, required_ids: set, current_manifest_sha256: str) -> RunEvaluation:
    run_meta_path = run_dir / "run_meta.json"
    if not run_meta_path.exists():
        return RunEvaluation(
            run_id=run_dir.name, structurally_complete=False,
            missing_required=sorted(required_ids), stale_manifest=False,
        )
    run_meta = read_json(run_meta_path)
    if run_meta.get("manifest_sha256") != current_manifest_sha256:
        return RunEvaluation(run_id=run_dir.name, structurally_complete=False, stale_manifest=True)

    present_ids = {p.name for p in run_dir.iterdir() if p.is_dir() and (p / "result.json").exists()}
    missing = sorted(required_ids - present_ids)
    if missing:
        return RunEvaluation(run_id=run_dir.name, structurally_complete=False, missing_required=missing)

    outcomes = {}
    for eid in required_ids:
        result = read_json(run_dir / eid / "result.json")
        outcomes[eid] = result["outcome"]

    run_invalid = sorted(eid for eid, o in outcomes.items() if o == "RUN_INVALID")
    failed = sorted(eid for eid, o in outcomes.items() if o == "FAIL")
    is_valid = not run_invalid
    functional_pass = is_valid and not failed

    return RunEvaluation(
        run_id=run_dir.name,
        structurally_complete=True,
        run_invalid_evals=run_invalid,
        failed_evals=failed,
        is_valid=is_valid,
        functional_pass=functional_pass,
    )


def valid_run_gate(workdir: "str | Path", runs_dir: "str | Path" = None, min_valid_runs: int = 1) -> GateResult:
    workdir = Path(workdir)

    if not is_frozen(workdir):
        return GateResult(
            gate=GATE_NAME, verdict="FAIL",
            reason="EVAL_MANIFEST not frozen - cannot evaluate runs against an unsnapshotted manifest",
        )

    manifest = load_yaml(canonical_manifest_path(workdir))
    required_ids = {e["eval_id"] for e in manifest.get("evals", []) if e.get("required", True)}
    current_manifest_sha256 = read_json(decision_input_manifest_path(workdir))["manifest_sha256"]

    runs_dir = Path(runs_dir) if runs_dir else workdir / "runs"
    run_dirs = discover_run_dirs(runs_dir)

    if not run_dirs:
        return GateResult(gate=GATE_NAME, verdict="FAIL", reason="no runs found", details={"runs_dir": str(runs_dir)})

    evaluations = [_evaluate_run(rd, required_ids, current_manifest_sha256) for rd in run_dirs]
    evidence = [
        {
            "run_id": ev.run_id,
            "structurally_complete": ev.structurally_complete,
            "missing_required": ev.missing_required,
            "stale_manifest": ev.stale_manifest,
            "run_invalid_evals": ev.run_invalid_evals,
            "failed_evals": ev.failed_evals,
        }
        for ev in evaluations
    ]

    incomplete = [ev for ev in evaluations if not ev.structurally_complete]
    if incomplete:
        stale = [ev.run_id for ev in incomplete if ev.stale_manifest]
        missing = [ev for ev in incomplete if not ev.stale_manifest]
        reason_parts = []
        if missing:
            reason_parts.append(
                "missing declared eval(s) in run(s): "
                + ", ".join(f"{ev.run_id}:{ev.missing_required}" for ev in missing)
            )
        if stale:
            reason_parts.append(f"run(s) executed against a stale (since re-frozen) manifest: {stale}")
        return GateResult(
            gate=GATE_NAME, verdict="FAIL", reason="; ".join(reason_parts), evidence=evidence,
        )

    valid_runs = [ev for ev in evaluations if ev.is_valid]
    if len(valid_runs) < min_valid_runs:
        return GateResult(
            gate=GATE_NAME, verdict="FAIL",
            reason=f"insufficient valid runs: {len(valid_runs)} < min_valid_runs={min_valid_runs} "
                   f"(RUN_INVALID runs never count toward this total)",
            evidence=evidence,
        )

    if not all(ev.functional_pass for ev in valid_runs):
        failing = [ev.run_id for ev in valid_runs if not ev.functional_pass]
        return GateResult(
            gate=GATE_NAME, verdict="FAIL",
            reason=f"functional assertion failure in valid run(s): {failing}",
            evidence=evidence,
        )

    return GateResult(
        gate=GATE_NAME, verdict="PASS",
        reason=f"{len(valid_runs)} valid run(s), all required evals PASS",
        evidence=evidence,
        details={"required_eval_ids": sorted(required_ids), "min_valid_runs": min_valid_runs},
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--runs-dir")
    parser.add_argument("--min-valid-runs", type=int, default=1)
    args = parser.parse_args(argv)

    result = valid_run_gate(args.workdir, runs_dir=args.runs_dir, min_valid_runs=args.min_valid_runs)
    print(f"{result.gate}: {result.verdict} - {result.reason}")
    return 0 if result.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
