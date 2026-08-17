from __future__ import annotations

import ast
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from rsc_common import GateResult  # noqa: E402
from package_release_gate import package_release_gate  # noqa: E402


def _pass(gate_name):
    return GateResult(gate=gate_name, verdict="PASS", reason="ok")


def _fail(gate_name):
    return GateResult(gate=gate_name, verdict="FAIL", reason="nope")


def test_blocked_without_valid_run_gate_pass():
    """Defect #6: PACKAGE_RELEASE_GATE must BLOCK when VALID_RUN_GATE did not
    PASS, even if ARTIFACT_INTEGRITY_GATE did."""
    result = package_release_gate(_fail("VALID_RUN_GATE"), _pass("ARTIFACT_INTEGRITY_GATE"))
    assert result.verdict == "BLOCKED"
    assert "VALID_RUN_GATE" in result.reason


def test_blocked_without_artifact_integrity_gate_pass():
    """Defect #6: PACKAGE_RELEASE_GATE must BLOCK when ARTIFACT_INTEGRITY_GATE
    did not PASS, even if VALID_RUN_GATE did."""
    result = package_release_gate(_pass("VALID_RUN_GATE"), _fail("ARTIFACT_INTEGRITY_GATE"))
    assert result.verdict == "BLOCKED"
    assert "ARTIFACT_INTEGRITY_GATE" in result.reason


def test_releasable_when_both_pass():
    result = package_release_gate(_pass("VALID_RUN_GATE"), _pass("ARTIFACT_INTEGRITY_GATE"))
    assert result.verdict == "RELEASABLE"


def test_inconclusive_when_a_subgate_result_is_missing():
    result = package_release_gate(None, _pass("ARTIFACT_INTEGRITY_GATE"))
    assert result.verdict == "INCONCLUSIVE"


def test_no_naming_ambiguity():
    """Defects #6/#11: the bare identifier `release_gate` must never appear
    anywhere in this module - not as a function name, not as a variable, not
    as an import alias. This is checked mechanically via an AST walk over
    Name, FunctionDef and arg nodes, not just asserted in a docstring.
    Docstring/comment prose mentioning the forbidden name (to explain the
    rule) is fine - only actual code identifiers are checked."""
    source = (SCRIPTS_DIR / "package_release_gate.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden = "release_gate"
    offending = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == forbidden:
            offending.append(("Name", node.lineno))
        elif isinstance(node, ast.FunctionDef) and node.name == forbidden:
            offending.append(("FunctionDef", node.lineno))
        elif isinstance(node, ast.arg) and node.arg == forbidden:
            offending.append(("arg", node.lineno))
        elif isinstance(node, ast.alias) and (node.asname == forbidden or node.name == forbidden):
            offending.append(("alias", node.lineno))

    assert offending == [], f"bare identifier {forbidden!r} found in code: {offending}"

    # Positive control: the module DOES define package_release_gate (a longer,
    # distinct identifier) - proving the AST walk actually finds real defs and
    # isn't just trivially passing on an empty file.
    assert any(
        isinstance(node, ast.FunctionDef) and node.name == "package_release_gate"
        for node in ast.walk(tree)
    )
