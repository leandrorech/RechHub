from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from snapshot_manager import freeze  # noqa: E402
from run_executor import execute_run  # noqa: E402
from package_release_gate import run_full_gate  # noqa: E402
from eval_isolation_check import eval_isolation_check  # noqa: E402


def _freeze(workdir):
    return freeze(
        workdir,
        eval_manifest=workdir / "eval_manifest.yaml",
        contract=workdir / "contract.yaml",
        candidate=workdir / "candidate",
    )


def test_full_pipeline_happy_path(pipeline_workdir):
    """Drives EVAL_ISOLATION -> SNAPSHOT -> RUN EXECUTION -> both gates ->
    PACKAGE_RELEASE_GATE end to end via the REAL subprocess-based
    run_executor (not the run_writer test shortcut), against the
    minimal_skill_pkg fixture. Final verdict must be RELEASABLE."""
    workdir = pipeline_workdir

    isolation = eval_isolation_check(workdir / "eval_manifest.yaml", scope="EVAL-A,EVAL-B")
    assert isolation["status"] == "PASS"

    _freeze(workdir)
    execute_run(workdir, "run-1")

    result = run_full_gate(workdir)
    assert result.verdict == "RELEASABLE", result.reason


def test_full_pipeline_blocked_path_on_post_snapshot_mutation(pipeline_workdir):
    """Same as the happy path, but the candidate is mutated AFTER the
    snapshot is frozen (and after the run executes) - the final verdict must
    flip to BLOCKED, citing ARTIFACT_INTEGRITY_GATE."""
    workdir = pipeline_workdir

    _freeze(workdir)
    execute_run(workdir, "run-1")

    # Mutate the candidate package after the snapshot was taken.
    (workdir / "candidate" / "scripts" / "noop.py").write_text("# tampered after snapshot\n")

    result = run_full_gate(workdir)
    assert result.verdict == "BLOCKED"
    assert "ARTIFACT_INTEGRITY_GATE" in result.reason


def test_full_pipeline_blocked_path_on_missing_run(pipeline_workdir):
    workdir = pipeline_workdir
    _freeze(workdir)
    # No run executed at all.
    result = run_full_gate(workdir)
    assert result.verdict == "BLOCKED"
    assert "VALID_RUN_GATE" in result.reason
