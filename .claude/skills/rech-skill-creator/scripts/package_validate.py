#!/usr/bin/env python3
"""package_validate.py - structural validation of a whole skill package
directory (SKILL.md presence/frontmatter, references/ and scripts/ file-type
rules, stray/hidden files, YAML well-formedness).

Defect #10 fix: ALL YAML in this module - including SKILL.md's frontmatter
block and any contract.yaml/eval_manifest.yaml under the package - is parsed
exclusively via rsc_common.load_yaml_str()/load_yaml() (PyYAML safe_load).
There is no hand-rolled line scanning anywhere in this file, so a multiline
block scalar (e.g. a `description: |` spanning several lines, one of which
contains a colon) is handled correctly instead of being misread as new
top-level structure.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import load_yaml, load_yaml_str  # noqa: E402

ALLOWED_REFERENCE_SUFFIXES = {".md"}
ALLOWED_SCRIPT_SUFFIXES = {".py"}


@dataclass
class PackageCheck:
    name: str
    status: str  # PASS | FAIL
    detail: str

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def parse_skill_md_frontmatter(skill_md_path: "str | Path"):
    """Extract and parse the `---\\n...\\n---` YAML frontmatter block from a
    SKILL.md file. Returns the parsed mapping, or None if no frontmatter block
    is found. Uses load_yaml_str() exclusively - correctly handles a
    multiline `description: |` or `description: >` block scalar."""
    text = Path(skill_md_path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm_text = text[3:end]
    return load_yaml_str(fm_text)


def validate_package(pkg_dir: "str | Path") -> list:
    pkg_dir = Path(pkg_dir)
    checks: list = []

    skill_md = pkg_dir / "SKILL.md"
    if not skill_md.exists():
        checks.append(PackageCheck("skill_md_present", "FAIL", "SKILL.md missing at package root"))
    else:
        checks.append(PackageCheck("skill_md_present", "PASS", str(skill_md)))
        try:
            frontmatter = parse_skill_md_frontmatter(skill_md)
        except Exception as exc:  # noqa: BLE001 - report as a failed check, not a crash
            checks.append(PackageCheck("frontmatter_parseable", "FAIL", f"YAML error: {exc}"))
            frontmatter = None
        else:
            if frontmatter is None:
                checks.append(PackageCheck("frontmatter_parseable", "FAIL", "no '---' frontmatter block found"))
            else:
                checks.append(PackageCheck("frontmatter_parseable", "PASS", "parsed via safe_load"))
                missing = [k for k in ("name", "description") if k not in frontmatter]
                checks.append(PackageCheck(
                    "frontmatter_required_fields",
                    "FAIL" if missing else "PASS",
                    f"missing: {missing}" if missing else "name+description present",
                ))
                if isinstance(frontmatter.get("description"), str):
                    length = len(frontmatter["description"])
                    checks.append(PackageCheck(
                        "description_length",
                        "PASS" if length <= 1024 else "FAIL",
                        f"{length} chars (limit 1024)",
                    ))

    references_dir = pkg_dir / "references"
    if references_dir.exists():
        bad = sorted(
            p.name for p in references_dir.iterdir()
            if p.is_file() and p.suffix.lower() not in ALLOWED_REFERENCE_SUFFIXES
        )
        checks.append(PackageCheck(
            "references_only_md", "FAIL" if bad else "PASS",
            f"disallowed file(s): {bad}" if bad else "all files are .md",
        ))

    scripts_dir = pkg_dir / "scripts"
    if scripts_dir.exists():
        bad = sorted(
            p.name for p in scripts_dir.iterdir()
            if p.is_file() and p.suffix.lower() not in ALLOWED_SCRIPT_SUFFIXES
        )
        checks.append(PackageCheck(
            "scripts_only_py", "FAIL" if bad else "PASS",
            f"disallowed file(s): {bad}" if bad else "all files are .py",
        ))

    stray = sorted(
        p.name for p in pkg_dir.iterdir()
        if p.is_file() and p.name not in ("SKILL.md",) and p.name.startswith(".")
    )
    checks.append(PackageCheck(
        "no_stray_hidden_files", "FAIL" if stray else "PASS",
        f"hidden file(s) at package root: {stray}" if stray else "none found",
    ))

    for yml in sorted(pkg_dir.glob("*.yaml")) + sorted(pkg_dir.glob("*.yml")):
        try:
            load_yaml(yml)
        except Exception as exc:  # noqa: BLE001
            checks.append(PackageCheck(f"yaml_well_formed:{yml.name}", "FAIL", str(exc)))
        else:
            checks.append(PackageCheck(f"yaml_well_formed:{yml.name}", "PASS", "parsed via safe_load"))

    return checks


def all_pass(checks: list) -> bool:
    return all(c.status == "PASS" for c in checks)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", required=True)
    args = parser.parse_args(argv)

    checks = validate_package(args.package_dir)
    ok = all_pass(checks)
    print(f"PACKAGE_VALIDATE: {'PASS' if ok else 'FAIL'}")
    for c in checks:
        print(f"  [{c.status}] {c.name}: {c.detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
