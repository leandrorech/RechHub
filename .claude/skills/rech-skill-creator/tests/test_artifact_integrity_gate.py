from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from snapshot_manager import freeze  # noqa: E402
from artifact_integrity_gate import artifact_integrity_gate  # noqa: E402


def _freeze(workdir, original=None, previous=None):
    return freeze(
        workdir,
        eval_manifest=workdir / "eval_manifest.yaml",
        contract=workdir / "contract.yaml",
        candidate=workdir / "candidate",
        original=original,
        previous=previous,
    )


def _freeze_with_history(workdir, tmp_path):
    original = tmp_path / "original"
    original.mkdir()
    (original / "f.txt").write_text("orig")
    previous = tmp_path / "previous"
    previous.mkdir()
    (previous / "f.txt").write_text("prev")
    _freeze(workdir, original=original, previous=previous)
    return original, previous


def test_no_snapshot_fails(pipeline_workdir):
    result = artifact_integrity_gate(pipeline_workdir)
    assert result.verdict == "FAIL"
    assert "no snapshot found" in result.reason


def test_happy_path_passes(pipeline_workdir, tmp_path):
    workdir = pipeline_workdir
    _freeze_with_history(workdir, tmp_path)
    result = artifact_integrity_gate(workdir)
    assert result.verdict == "PASS"


def test_manifest_mutation_after_snapshot_detected(pipeline_workdir, tmp_path):
    """Defects #1/#8 companion check: once frozen, any real change to the
    manifest content (not just cosmetic re-formatting) must be detected, and
    - because eval_manifest.yaml lives OUTSIDE candidate/ in this fixture -
    must be reported as EVAL_MANIFEST specifically, not conflated with
    CANDIDATE."""
    workdir = pipeline_workdir
    _freeze_with_history(workdir, tmp_path)

    manifest_path = workdir / "eval_manifest.yaml"
    manifest_path.write_text(manifest_path.read_text().replace('"minimal-skill"', '"mutated-skill"'))

    result = artifact_integrity_gate(workdir)
    assert result.verdict == "FAIL"
    changed = {p["category"] for p in result.evidence if p.get("status") == "CHANGED"}
    assert changed == {"EVAL_MANIFEST"}


def test_cosmetic_reformatting_of_manifest_is_not_flagged(pipeline_workdir, tmp_path):
    """Whitespace/comment-only edits must NOT register as a content change -
    the hash is over canonicalized parsed content, not raw bytes."""
    workdir = pipeline_workdir
    _freeze_with_history(workdir, tmp_path)

    manifest_path = workdir / "eval_manifest.yaml"
    manifest_path.write_text(manifest_path.read_text() + "\n\n# a trailing comment, no value changed\n")

    result = artifact_integrity_gate(workdir)
    assert result.verdict == "PASS"


def test_run_execution_after_snapshot_does_not_perturb_candidate(pipeline_workdir, tmp_path):
    """runs/ is created by run_executor AFTER the snapshot - it must never be
    part of what CANDIDATE's hash covers, or every pipeline run would
    spuriously self-invalidate its own snapshot."""
    workdir = pipeline_workdir
    _freeze_with_history(workdir, tmp_path)

    sys.path.insert(0, str(SCRIPTS_DIR))
    from run_executor import execute_run  # noqa: E402

    execute_run(workdir, "run-1")

    result = artifact_integrity_gate(workdir)
    assert result.verdict == "PASS"


@pytest.mark.parametrize("category", ["ORIGINAL", "PREVIOUS", "CANDIDATE", "EVAL_MANIFEST", "CONTRACT"])
def test_integrity_covers_all_named_inputs(category, pipeline_workdir, tmp_path):
    """Defect #3: ARTIFACT_INTEGRITY_GATE protects ALL decision inputs, not
    just CANDIDATE. Mutate exactly one category at a time and confirm the
    gate names that specific category, and ONLY that category - proving there
    is no special-cased code path that only watches CANDIDATE, and no
    accidental coupling between the categories."""
    workdir = pipeline_workdir
    original, previous = _freeze_with_history(workdir, tmp_path)

    if category == "ORIGINAL":
        (original / "f.txt").write_text("MUTATED")
    elif category == "PREVIOUS":
        (previous / "f.txt").write_text("MUTATED")
    elif category == "CANDIDATE":
        (workdir / "candidate" / "scripts" / "noop.py").write_text("# mutated candidate content\n")
    elif category == "EVAL_MANIFEST":
        p = workdir / "eval_manifest.yaml"
        p.write_text(p.read_text().replace('"minimal-skill"', '"mutated-skill"'))
    elif category == "CONTRACT":
        p = workdir / "contract.yaml"
        p.write_text(p.read_text().replace('version: "0.1.0"', 'version: "0.2.0"'))

    result = artifact_integrity_gate(workdir)
    assert result.verdict == "FAIL"
    flagged = {p["category"] for p in result.evidence if p.get("status") in ("CHANGED", "MISSING")}
    assert flagged == {category}, f"expected only {category} flagged, got {flagged}"


def test_missing_candidate_directory_detected(pipeline_workdir, tmp_path):
    workdir = pipeline_workdir
    _freeze_with_history(workdir, tmp_path)
    import shutil

    shutil.rmtree(workdir / "candidate" / "scripts")
    result = artifact_integrity_gate(workdir)
    assert result.verdict == "FAIL"
    flagged = {p["category"] for p in result.evidence}
    assert flagged == {"CANDIDATE"}
