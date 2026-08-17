#!/usr/bin/env python3
"""package_release_gate.py - composes VALID_RUN_GATE and ARTIFACT_INTEGRITY_GATE
into the final packaging decision (defects #6, #11).

Verdict vocabulary: RELEASABLE | BLOCKED | INCONCLUSIVE.

  RELEASABLE   - both sub-gates ran and both returned PASS.
  BLOCKED      - at least one sub-gate ran and returned FAIL. The reason names
                 exactly which sub-gate blocked release.
  INCONCLUSIVE - a sub-gate result could not be obtained at all (e.g. the
                 caller could not even produce a verdict for it - not the same
                 as the sub-gate itself returning FAIL).

Naming note (defects #6/#11): this module, its function, its CLI subcommand
and its JSON output key are always the literal string "PACKAGE_RELEASE_GATE" -
never aliased to or referred to internally as just "release_gate", which would
collide conceptually with the unrelated, already-locked sibling skill
rech-release-gate (that skill decides RECH *product* release readiness; this
one decides whether a *skill package* is releasable - two different
questions, not two names for the same gate).
test_package_release_gate.py::test_no_naming_ambiguity enforces this
mechanically via an AST walk, not just this docstring promise.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import GateResult  # noqa: E402
from artifact_integrity_gate import artifact_integrity_gate  # noqa: E402
from valid_run_gate import valid_run_gate  # noqa: E402

GATE_NAME = "PACKAGE_RELEASE_GATE"


def package_release_gate(
    valid_run_gate_result: GateResult | None,
    artifact_integrity_gate_result: GateResult | None,
) -> GateResult:
    if valid_run_gate_result is None or artifact_integrity_gate_result is None:
        missing = [
            name
            for name, val in (
                ("VALID_RUN_GATE", valid_run_gate_result),
                ("ARTIFACT_INTEGRITY_GATE", artifact_integrity_gate_result),
            )
            if val is None
        ]
        return GateResult(
            gate=GATE_NAME, verdict="INCONCLUSIVE",
            reason=f"sub-gate result unavailable: {missing}",
        )

    if valid_run_gate_result.verdict != "PASS":
        return GateResult(
            gate=GATE_NAME, verdict="BLOCKED",
            reason=f"VALID_RUN_GATE={valid_run_gate_result.verdict}: {valid_run_gate_result.reason}",
            evidence=[valid_run_gate_result.to_dict()],
        )

    if artifact_integrity_gate_result.verdict != "PASS":
        return GateResult(
            gate=GATE_NAME, verdict="BLOCKED",
            reason=f"ARTIFACT_INTEGRITY_GATE={artifact_integrity_gate_result.verdict}: "
                   f"{artifact_integrity_gate_result.reason}",
            evidence=[artifact_integrity_gate_result.to_dict()],
        )

    return GateResult(
        gate=GATE_NAME, verdict="RELEASABLE",
        reason="VALID_RUN_GATE and ARTIFACT_INTEGRITY_GATE both PASS",
        evidence=[valid_run_gate_result.to_dict(), artifact_integrity_gate_result.to_dict()],
    )


def run_full_gate(workdir: "str | Path", runs_dir: "str | Path" = None, min_valid_runs: int = 1) -> GateResult:
    """Convenience composition: runs both sub-gates against `workdir` and
    feeds their results into package_release_gate(). Used by the CLI and by
    the end-to-end pipeline test."""
    vr = valid_run_gate(workdir, runs_dir=runs_dir, min_valid_runs=min_valid_runs)
    ai = artifact_integrity_gate(workdir)
    return package_release_gate(vr, ai)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--runs-dir")
    parser.add_argument("--min-valid-runs", type=int, default=1)
    args = parser.parse_args(argv)

    result = run_full_gate(args.workdir, runs_dir=args.runs_dir, min_valid_runs=args.min_valid_runs)
    print(f"{result.gate}: {result.verdict} - {result.reason}")
    return 0 if result.verdict == "RELEASABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
