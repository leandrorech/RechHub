from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from skills_api_validate import overall_status, skills_api_validate  # noqa: E402

SKILLS_ROOT = Path(__file__).resolve().parents[2]  # .../.claude/skills


def test_no_bare_pass_without_evidence(workdir):
    """Defect #4: every check row must carry non-empty evidence, and the
    genuinely-unreachable checks (upload_registration, live_routing) must be
    present and explicitly NOT_APPLICABLE - never silently dropped, never
    promoted to PASS."""
    checks = skills_api_validate(workdir)

    assert all(c.detail for c in checks), "every check must carry non-empty evidence"

    by_name = {c.name: c for c in checks}
    assert by_name["upload_registration"].status == "NOT_APPLICABLE"
    assert by_name["live_routing"].status == "NOT_APPLICABLE"
    assert "network" in by_name["upload_registration"].detail.lower()


def test_missing_skills_root_yields_partial_not_pass(workdir):
    """Omitting skills_root leaves internal_link_check UNVERIFIED, which must
    prevent a clean overall PASS - never silently absorbed."""
    checks = skills_api_validate(workdir, skills_root=None)
    by_name = {c.name: c for c in checks}
    assert by_name["internal_link_check"].status == "UNVERIFIED"
    assert overall_status(checks) != "PASS"


def test_full_offline_pass_reachable_with_all_inputs(workdir):
    """With every offline-checkable input actually supplied (skills_root
    given, redirect_to='none' in the fixture contract), overall_status() must
    be able to reach a genuine PASS - proving the checker is not permanently
    stuck below PASS regardless of input quality, which would be just as
    untrustworthy as a checker that always fakes PASS."""
    checks = skills_api_validate(workdir, skills_root=SKILLS_ROOT)
    by_name = {c.name: c for c in checks}
    assert by_name["internal_link_check"].status == "PASS"
    assert overall_status(checks) == "PASS"


def test_bad_naming_fails(workdir, tmp_path):
    import shutil

    bad_dir = tmp_path / "Bad_Name_Not_Kebab"
    shutil.copytree(workdir, bad_dir)
    checks = skills_api_validate(bad_dir)
    by_name = {c.name: c for c in checks}
    assert by_name["naming_rules"].status == "FAIL"
    assert overall_status(checks) == "FAIL"


def test_unresolved_redirect_fails(workdir, tmp_path):
    contract_path = workdir / "contract.yaml"
    contract_path.write_text(
        contract_path.read_text().replace('redirect_to: "none"', 'redirect_to: "does-not-exist-anywhere"')
    )
    checks = skills_api_validate(workdir, skills_root=SKILLS_ROOT)
    by_name = {c.name: c for c in checks}
    assert by_name["internal_link_check"].status == "FAIL"
    assert overall_status(checks) == "FAIL"
