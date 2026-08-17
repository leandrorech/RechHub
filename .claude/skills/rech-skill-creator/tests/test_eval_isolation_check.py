from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from eval_isolation_check import eval_isolation_check  # noqa: E402


def test_missing_scope_yields_unverified_not_pass(with_valid_manifest):
    """Defect #7: omitting --scope must never yield PASS."""
    result = eval_isolation_check(with_valid_manifest / "eval_manifest.yaml", scope=None)
    assert result["status"] == "UNVERIFIED"
    assert result["status"] != "PASS"
    # diagnostic-only suggestion may be attached, but must never satisfy PASS
    assert "suggested_scope_diagnostic_only" in result


def test_empty_scope_string_yields_unverified(with_valid_manifest):
    result = eval_isolation_check(with_valid_manifest / "eval_manifest.yaml", scope="   ,  ")
    assert result["status"] == "UNVERIFIED"


def test_insufficient_scope_yields_partial_not_pass(with_valid_manifest):
    """Scope covering only part of the required evals must never yield PASS."""
    result = eval_isolation_check(with_valid_manifest / "eval_manifest.yaml", scope="EVAL-A")
    assert result["status"] == "PARTIAL"
    assert result["status"] != "PASS"


def test_full_scope_yields_pass(with_valid_manifest):
    result = eval_isolation_check(with_valid_manifest / "eval_manifest.yaml", scope="EVAL-A,EVAL-B")
    assert result["status"] == "PASS"
    assert result["scope"] == ["EVAL-A", "EVAL-B"]


def test_overlap_detected_yields_partial(with_valid_manifest):
    manifest_path = with_valid_manifest / "eval_manifest.yaml"
    text = manifest_path.read_text()
    # Give both evals the same declared shared_resource - a real overlap.
    text = text.replace(
        'input:\n      cmd: ["python3", "-c", "print(\'A-ok\')"]',
        'input:\n      cmd: ["python3", "-c", "print(\'A-ok\')"]\n      shared_resource: "tmp/shared.lock"',
    ).replace(
        'input:\n      cmd: ["python3", "-c", "print(\'B-ok\')"]',
        'input:\n      cmd: ["python3", "-c", "print(\'B-ok\')"]\n      shared_resource: "tmp/shared.lock"',
    )
    manifest_path.write_text(text)

    result = eval_isolation_check(manifest_path, scope="EVAL-A,EVAL-B")
    assert result["status"] == "PARTIAL"
    assert "overlap" in result["reason"].lower()
