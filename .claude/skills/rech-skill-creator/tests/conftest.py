from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

from rsc_common import now_iso, write_json  # noqa: E402


@pytest.fixture
def minimal_pkg_src() -> Path:
    return FIXTURES_DIR / "minimal_skill_pkg"


@pytest.fixture
def workdir(tmp_path, minimal_pkg_src) -> Path:
    """A fresh, isolated copy of the minimal skill package fixture, used as
    both the CANDIDATE directory and the general working directory (where
    eval_manifest.yaml, contract.yaml, snapshot/, and runs/ all live).

    Named `minimal-skill` (matching SKILL.md's own frontmatter `name` field
    and contract.yaml's `skill_id`), not a generic `workdir` - a real skill
    package's directory name always matches its declared name, and
    skills_api_validate.py's frontmatter_name_matches_dir check correctly
    enforces that, so the fixture needs to satisfy it like any real package."""
    dest = tmp_path / "minimal-skill"
    shutil.copytree(minimal_pkg_src, dest)
    return dest


@pytest.fixture
def eval_manifest_valid_path() -> Path:
    return FIXTURES_DIR / "eval_manifest_valid.yaml"


@pytest.fixture
def eval_manifest_multiline_path() -> Path:
    return FIXTURES_DIR / "eval_manifest_multiline.yaml"


@pytest.fixture
def with_valid_manifest(workdir, eval_manifest_valid_path) -> Path:
    """Copies eval_manifest_valid.yaml (2 required evals: EVAL-A, EVAL-B) into
    `workdir` and returns the workdir path. Used by tests that only need
    package-level structural validation, not the gate/pipeline scripts."""
    shutil.copy(eval_manifest_valid_path, workdir / "eval_manifest.yaml")
    return workdir


@pytest.fixture
def pipeline_workdir(tmp_path, minimal_pkg_src, eval_manifest_valid_path) -> Path:
    """A pipeline build directory with CANDIDATE genuinely isolated from the
    harness's own bookkeeping files, matching how ARTIFACT_INTEGRITY_GATE's
    decision-input categories are meant to be independent:

        pipeline_workdir/
        |-- eval_manifest.yaml   (EVAL_MANIFEST - independent input)
        |-- contract.yaml        (CONTRACT - independent input)
        |-- candidate/           (CANDIDATE - just the skill's own files;
        |   |-- SKILL.md          no contract.yaml, no eval_manifest.yaml,
        |   |-- references/       so mutating either of those never touches
        |   `-- scripts/          the CANDIDATE hash)
        |-- snapshot/            (created by snapshot_manager.freeze())
        `-- runs/                (created by run_executor.execute_run())

    A flat layout (everything under one directory, CANDIDATE = the whole
    thing) was tried first and rejected: it made eval_manifest.yaml part of
    CANDIDATE's own hash (so a purely cosmetic manifest edit still changed
    CANDIDATE), and made `runs/` - created by run_executor AFTER the
    snapshot - retroactively change CANDIDATE's hash simply by existing.
    Both are exactly the kind of accidental coupling ARTIFACT_INTEGRITY_GATE's
    per-category design (defect #3) is supposed to prevent.
    """
    root = tmp_path / "pipeline_workdir"
    candidate = root / "candidate"
    shutil.copytree(minimal_pkg_src, candidate)
    (candidate / "contract.yaml").unlink()
    shutil.copy(minimal_pkg_src / "contract.yaml", root / "contract.yaml")
    shutil.copy(eval_manifest_valid_path, root / "eval_manifest.yaml")
    return root


def write_run(run_dir: Path, manifest_sha256: str, outcomes: dict, details: dict | None = None) -> None:
    """Directly write a run-N/ directory matching run_executor.py's on-disk
    schema (run_meta.json + <eval_id>/result.json per eval), for gate-level
    tests that need precise, deterministic control over per-eval outcomes
    (e.g. forcing RUN_INVALID, or omitting a required eval entirely) without
    depending on real subprocess execution timing/behavior.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    eval_ids = []
    for eval_id, outcome in outcomes.items():
        eval_ids.append(eval_id)
        eval_dir = run_dir / eval_id
        eval_dir.mkdir(parents=True, exist_ok=True)
        write_json(
            eval_dir / "result.json",
            {
                "eval_id": eval_id,
                "outcome": outcome,
                "manifest_sha256": manifest_sha256,
                "executed_at": now_iso(),
                "details": (details or {}).get(eval_id, {}),
            },
        )
    write_json(
        run_dir / "run_meta.json",
        {
            "run_id": run_dir.name,
            "manifest_sha256": manifest_sha256,
            "manifest_id": "test-manifest-id",
            "created_at": now_iso(),
            "eval_ids": eval_ids,
        },
    )


@pytest.fixture
def run_writer():
    return write_run
