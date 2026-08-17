from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from snapshot_manager import freeze  # noqa: E402
from valid_run_gate import valid_run_gate  # noqa: E402


def _freeze(workdir):
    result = freeze(workdir, eval_manifest=workdir / "eval_manifest.yaml", contract=workdir / "contract.yaml")
    return result["manifest_sha256"]


def test_missing_required_eval_blocks_gate(with_valid_manifest, run_writer):
    """Defect #2: a declared eval missing from a run FAILs the gate, never
    silently skipped or ignored."""
    workdir = with_valid_manifest
    manifest_sha256 = _freeze(workdir)

    # Only EVAL-A is present; EVAL-B (also required) is missing entirely.
    run_writer(workdir / "runs" / "run-1", manifest_sha256, {"EVAL-A": "PASS"})

    result = valid_run_gate(workdir)
    assert result.verdict == "FAIL"
    assert "missing declared eval" in result.reason
    assert "EVAL-B" in result.reason


def test_run_invalid_not_counted_as_pass(with_valid_manifest, run_writer):
    """RUN_INVALID (timeout/infra exception) is a third bucket: never counted
    as a functional PASS, and the run is excluded from the valid-run pool
    entirely (not counted as a functional FAIL either)."""
    workdir = with_valid_manifest
    manifest_sha256 = _freeze(workdir)

    run_writer(workdir / "runs" / "run-1", manifest_sha256, {"EVAL-A": "PASS", "EVAL-B": "RUN_INVALID"})

    result = valid_run_gate(workdir, min_valid_runs=1)
    assert result.verdict == "FAIL"
    assert "insufficient valid runs" in result.reason
    # The run must be reported present (structurally complete) but invalid -
    # never silently absent from the evidence, and never described as PASS.
    run1_evidence = next(e for e in result.evidence if e["run_id"] == "run-1")
    assert run1_evidence["structurally_complete"] is True
    assert "EVAL-B" in run1_evidence["run_invalid_evals"]
    assert "PASS" not in result.reason.upper().replace("INVALID", "")  # sanity: no stray claim of pass


def test_run_invalid_does_not_count_toward_min_valid_runs_even_with_other_valid_runs(with_valid_manifest, run_writer):
    workdir = with_valid_manifest
    manifest_sha256 = _freeze(workdir)

    run_writer(workdir / "runs" / "run-1", manifest_sha256, {"EVAL-A": "RUN_INVALID", "EVAL-B": "PASS"})
    run_writer(workdir / "runs" / "run-2", manifest_sha256, {"EVAL-A": "PASS", "EVAL-B": "PASS"})

    result = valid_run_gate(workdir, min_valid_runs=1)
    assert result.verdict == "PASS"
    run1_evidence = next(e for e in result.evidence if e["run_id"] == "run-1")
    run2_evidence = next(e for e in result.evidence if e["run_id"] == "run-2")
    assert run1_evidence["run_invalid_evals"] == ["EVAL-A"]
    assert run2_evidence["run_invalid_evals"] == []


def test_functional_failure_blocks_gate(with_valid_manifest, run_writer):
    workdir = with_valid_manifest
    manifest_sha256 = _freeze(workdir)
    run_writer(workdir / "runs" / "run-1", manifest_sha256, {"EVAL-A": "PASS", "EVAL-B": "FAIL"})

    result = valid_run_gate(workdir)
    assert result.verdict == "FAIL"
    assert "functional assertion failure" in result.reason


def test_happy_path_passes(with_valid_manifest, run_writer):
    workdir = with_valid_manifest
    manifest_sha256 = _freeze(workdir)
    run_writer(workdir / "runs" / "run-1", manifest_sha256, {"EVAL-A": "PASS", "EVAL-B": "PASS"})

    result = valid_run_gate(workdir)
    assert result.verdict == "PASS"


def test_no_runs_fails(with_valid_manifest):
    workdir = with_valid_manifest
    _freeze(workdir)
    result = valid_run_gate(workdir)
    assert result.verdict == "FAIL"
    assert "no runs found" in result.reason


def test_unfrozen_manifest_fails(with_valid_manifest):
    workdir = with_valid_manifest
    result = valid_run_gate(workdir)
    assert result.verdict == "FAIL"
    assert "not frozen" in result.reason


def test_stale_manifest_run_is_rejected(with_valid_manifest, run_writer):
    """A run executed against an OLDER frozen manifest must not be silently
    accepted just because its eval outcomes happen to be present - it is
    structurally incomplete against the CURRENT snapshot."""
    workdir = with_valid_manifest
    manifest_path = workdir / "eval_manifest.yaml"

    stale_sha256 = _freeze(workdir)
    run_writer(workdir / "runs" / "run-1", stale_sha256, {"EVAL-A": "PASS", "EVAL-B": "PASS"})

    # Re-freeze with a real content change - this is now a DIFFERENT manifest.
    manifest_path.write_text(manifest_path.read_text().replace('"minimal-skill"', '"mutated-skill"'))
    fresh_sha256 = _freeze(workdir)
    assert fresh_sha256 != stale_sha256

    result = valid_run_gate(workdir)
    assert result.verdict == "FAIL"
    assert "stale" in result.reason.lower()
    run1 = next(e for e in result.evidence if e["run_id"] == "run-1")
    assert run1["stale_manifest"] is True
