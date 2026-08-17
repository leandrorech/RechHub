from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from rsc_common import load_yaml  # noqa: E402
from package_validate import all_pass, validate_package  # noqa: E402


def test_multiline_block_scalar_parsed_correctly(eval_manifest_multiline_path):
    """Defect #10: a `|` block scalar containing a decoy line that looks like
    a YAML key ("assertions: ...") must be parsed as literal text, never
    promoted to real document structure."""
    data = load_yaml(eval_manifest_multiline_path)

    assert set(data.keys()) == {"manifest_version", "skill_under_test", "skill_version", "evals", "metadata"}

    description = data["evals"][0]["description"]
    expected = (
        "Multi-line description text spanning several lines.\n"
        "Note: this line contains a colon and must stay literal content.\n"
        "assertions: this looks exactly like a YAML key but is NOT one - it is\n"
        "plain text inside a block scalar and must never be promoted to real\n"
        "document structure by a correct parser.\n"
    )
    assert description == expected

    # The real `assertions` field (a sibling key, not the decoy text) must
    # still be its own structured list, untouched by the decoy line.
    assert isinstance(data["evals"][0]["assertions"], list)
    assert data["evals"][0]["assertions"][0]["type"] == "exit_code"


def test_minimal_pkg_fixture_passes_structural_validation(workdir):
    checks = validate_package(workdir)
    assert all_pass(checks), [c.to_dict() for c in checks if c.status != "PASS"]


def test_missing_skill_md_fails(tmp_path):
    (tmp_path / "references").mkdir()
    checks = validate_package(tmp_path)
    by_name = {c.name: c for c in checks}
    assert by_name["skill_md_present"].status == "FAIL"


def test_disallowed_file_in_scripts_fails(workdir):
    (workdir / "scripts" / "not-a-script.txt").write_text("stray")
    checks = validate_package(workdir)
    by_name = {c.name: c for c in checks}
    assert by_name["scripts_only_py"].status == "FAIL"
    assert "not-a-script.txt" in by_name["scripts_only_py"].detail


def test_stray_hidden_file_fails(workdir):
    (workdir / ".DS_Store").write_text("junk")
    checks = validate_package(workdir)
    by_name = {c.name: c for c in checks}
    assert by_name["no_stray_hidden_files"].status == "FAIL"
