#!/usr/bin/env python3
"""skills_api_validate.py - Skills-API-shaped validation, restricted to what
can actually be mechanically checked offline in this sandbox (defect #4:
never emit a placeholder empty PASS - every row is either a real PASS/FAIL
with evidence, or an explicit UNVERIFIED/NOT_APPLICABLE).

Offline-checkable (built on package_validate.py's generic structural checks,
plus Skills-API-specific rows added here): frontmatter fields, description
length/charset, naming rules, file structure, YAML well-formedness, internal
redirect_to links.

NOT checkable at all in this offline sandbox, always reported NOT_APPLICABLE,
never silently promoted to PASS: upload_registration, live_routing, and
size_report (reported as a fact for reference - no documented size-limit
constant exists here to score against, so there is nothing to pass or fail).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import load_yaml  # noqa: E402
from package_validate import parse_skill_md_frontmatter, validate_package  # noqa: E402

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@dataclass
class ApiCheck:
    name: str
    status: str  # PASS | FAIL | UNVERIFIED | NOT_APPLICABLE
    detail: str

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def skills_api_validate(pkg_dir: "str | Path", skills_root: "str | Path" = None) -> list:
    pkg_dir = Path(pkg_dir)
    checks: list = []

    for c in validate_package(pkg_dir):
        checks.append(ApiCheck(c.name, c.status, c.detail))

    dir_name = pkg_dir.name
    name_ok = bool(NAME_PATTERN.match(dir_name))
    checks.append(ApiCheck(
        "naming_rules", "PASS" if name_ok else "FAIL",
        f"directory name {dir_name!r} {'matches' if name_ok else 'does NOT match'} ^[a-z0-9]+(-[a-z0-9]+)*$",
    ))

    skill_md = pkg_dir / "SKILL.md"
    frontmatter = None
    if skill_md.exists():
        try:
            frontmatter = parse_skill_md_frontmatter(skill_md)
        except Exception:  # noqa: BLE001
            frontmatter = None

    if frontmatter and isinstance(frontmatter.get("description"), str):
        desc = frontmatter["description"]
        printable_ok = all(ch.isprintable() or ch in "\n\t" for ch in desc)
        checks.append(ApiCheck(
            "description_charset", "PASS" if printable_ok else "FAIL",
            "utf-8, printable" if printable_ok else "contains non-printable/control characters",
        ))
        fm_name = frontmatter.get("name")
        checks.append(ApiCheck(
            "frontmatter_name_matches_dir", "PASS" if fm_name == dir_name else "FAIL",
            f"frontmatter name={fm_name!r} vs directory={dir_name!r}",
        ))

    contract_path = pkg_dir / "contract.yaml"
    if skills_root is not None and contract_path.exists():
        skills_root = Path(skills_root)
        sibling_dirs = {p.name for p in skills_root.iterdir() if p.is_dir()}
        try:
            contract = load_yaml(contract_path) or {}
        except Exception:  # noqa: BLE001
            contract = {}
        redirects = [
            nt.get("redirect_to")
            for nt in (contract.get("when_to_use") or {}).get("negative_triggers", [])
            if isinstance(nt, dict)
        ]
        unresolved = sorted({r for r in redirects if r and r != "none" and r not in sibling_dirs})
        checks.append(ApiCheck(
            "internal_link_check", "FAIL" if unresolved else "PASS",
            f"unresolved redirect_to target(s): {unresolved}" if unresolved
            else "all redirect_to values resolve to a sibling directory or are 'none'",
        ))
    elif contract_path.exists():
        checks.append(ApiCheck(
            "internal_link_check", "UNVERIFIED",
            "contract.yaml exists but no skills_root was supplied to resolve redirect_to links",
        ))
    else:
        checks.append(ApiCheck(
            "internal_link_check", "NOT_APPLICABLE",
            "no concrete contract.yaml; contract_template.yaml placeholders are not runtime redirect declarations",
        ))

    # NOT_APPLICABLE (not UNVERIFIED): there is no documented size-limit constant
    # in this sandbox to score against at all, ever - this isn't a transient gap
    # that more input could resolve, so it's out of scope the same way a live
    # network check is, not a pending "give me more input and I can check it".
    total_bytes = sum(f.stat().st_size for f in pkg_dir.rglob("*") if f.is_file())
    checks.append(ApiCheck(
        "size_report", "NOT_APPLICABLE",
        f"{total_bytes} bytes total, reported for reference only - no documented size threshold "
        f"exists in this sandbox to score against",
    ))

    checks.append(ApiCheck(
        "upload_registration", "NOT_APPLICABLE",
        "requires a live Skills API network call; not available in this offline sandbox",
    ))
    checks.append(ApiCheck(
        "live_routing", "NOT_APPLICABLE",
        "requires an actual Claude session selecting among competing skills; not available in this offline sandbox",
    ))

    return checks


def overall_status(checks: list) -> str:
    """FAIL takes precedence over everything. Any UNVERIFIED row (something
    that genuinely could not be checked) prevents a clean PASS - this is the
    concrete mechanism preventing defect #4's placeholder-PASS: an unresolved
    UNVERIFIED item can never be silently absorbed into an overall PASS.
    NOT_APPLICABLE rows are explicitly out of offline scope and do not block
    PASS on their own."""
    statuses = {c.status for c in checks}
    if "FAIL" in statuses:
        return "FAIL"
    if "UNVERIFIED" in statuses:
        return "PARTIAL"
    return "PASS"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--skills-root")
    args = parser.parse_args(argv)

    checks = skills_api_validate(args.package_dir, skills_root=args.skills_root)
    overall = overall_status(checks)
    print(f"SKILLS_API: {overall}")
    for c in checks:
        print(f"  [{c.status}] {c.name}: {c.detail}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
