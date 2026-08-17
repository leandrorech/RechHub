from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from snapshot_manager import (  # noqa: E402
    canonical_manifest_path,
    decision_input_manifest_path,
    freeze,
    is_frozen,
)
from run_executor import execute_run  # noqa: E402
from rsc_common import read_json  # noqa: E402


def _freeze(workdir):
    return freeze(
        workdir,
        eval_manifest=workdir / "eval_manifest.yaml",
        contract=workdir / "contract.yaml",
        candidate=workdir / "candidate",
    )


def test_manifest_snapshot_created_before_run_executor_can_run(pipeline_workdir):
    """Defects #1/#8: EVAL_MANIFEST must be frozen/hashed BEFORE any run
    executes. Structural proof: run_executor refuses outright while unfrozen,
    and succeeds only after snapshot_manager.freeze() has run."""
    workdir = pipeline_workdir

    assert not is_frozen(workdir)

    with pytest.raises(RuntimeError, match="not frozen"):
        execute_run(workdir, "run-1")

    result = _freeze(workdir)

    assert is_frozen(workdir)
    assert canonical_manifest_path(workdir).exists()
    assert decision_input_manifest_path(workdir).exists()
    assert result["manifest_id"]
    assert result["manifest_sha256"]

    exec_result = execute_run(workdir, "run-1")
    assert exec_result["run_meta"]["run_id"] == "run-1"
    assert set(exec_result["evals"].keys()) == {"EVAL-A", "EVAL-B"}


def test_freeze_writes_decision_input_manifest_with_all_categories(pipeline_workdir):
    workdir = pipeline_workdir
    _freeze(workdir)
    stored = read_json(decision_input_manifest_path(workdir))
    assert set(stored["inputs"].keys()) == {
        "ORIGINAL", "PREVIOUS", "CANDIDATE", "EVAL_MANIFEST", "CONTRACT",
        "EVAL_DEFINITIONS_FIXTURES", "CONFIG",
    }
    # ORIGINAL/PREVIOUS undeclared -> explicit absence, not omission.
    assert stored["inputs"]["ORIGINAL"] == {"path": None, "kind": "none", "sha256": None}
    assert stored["inputs"]["PREVIOUS"] == {"path": None, "kind": "none", "sha256": None}
    assert stored["inputs"]["CANDIDATE"]["kind"] == "directory"
    assert stored["inputs"]["CANDIDATE"]["sha256"]
    assert stored["inputs"]["CONFIG"]["declared"] is False


def test_freeze_is_deterministic_for_unchanged_content(pipeline_workdir):
    """Cosmetic re-serialization must not change the manifest hash - the hash
    is over canonicalized content, not raw bytes/whitespace."""
    workdir = pipeline_workdir
    r1 = _freeze(workdir)
    r2 = _freeze(workdir)
    assert r1["manifest_sha256"] == r2["manifest_sha256"]
    assert r1["inputs"]["CANDIDATE"]["sha256"] == r2["inputs"]["CANDIDATE"]["sha256"]
