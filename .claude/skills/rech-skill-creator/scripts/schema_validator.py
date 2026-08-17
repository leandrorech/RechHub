#!/usr/bin/env python3
"""schema_validator.py - validates a `contract.yaml` instance against the
shape defined in `contract_template.yaml` (defect #5: the template is the
full approved contract, checked here to actually contain every required key
- not just asserted in prose). Also validates that `metadata` is accepted
(defect #9).

Severity and evidence-level fields are validated against the RAF scale only
(references/finding-schema-and-raf-mapping.md in rech-deep-audit) - this
module introduces no classification vocabulary of its own.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import load_yaml  # noqa: E402

REQUIRED_TOP_LEVEL_KEYS = [
    "skill_id",
    "name",
    "version",
    "goal",
    "when_to_use",
    "input_contract",
    "output_contract",
    "skill_schema",
    "execution_environment",
    "risk_side_effects",
    "hard_constraints",
    "preferred_constraints",
    "current_constraints",
    "non_goals",
    "invariants",
    "failure_modes",
    "evidence_required",
    "metadata",
]

# RAF scale only - never extend this set with a parallel taxonomy.
RAF_SEVERITY = {"BLOCKER", "CRITICAL", "HIGH", "MEDIUM", "LOW"}
RAF_EVIDENCE_LEVELS = {f"E{i}" for i in range(6)}  # E0-E5
RAF_EVIDENCE_LEVELS_NOT_TEXTUALLY_CONFIRMED = {"E0", "E5"}


@dataclass
class ValidationResult:
    valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"valid": self.valid, "errors": self.errors, "warnings": self.warnings}


def validate_contract(data: dict) -> ValidationResult:
    errors: list = []
    warnings: list = []

    if not isinstance(data, dict):
        return ValidationResult(valid=False, errors=["contract root must be a mapping"])

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"missing required top-level key: {key}")

    if "metadata" in data and not isinstance(data["metadata"], dict):
        errors.append("metadata must be a mapping")

    for inv in (data.get("invariants") or []):
        sev = inv.get("severity")
        if sev and sev not in RAF_SEVERITY:
            errors.append(
                f"invariant {inv.get('id', '?')!r}: severity {sev!r} not in RAF scale {sorted(RAF_SEVERITY)}"
            )

    for fm in (data.get("failure_modes") or []):
        sev = fm.get("severity")
        if sev and sev not in RAF_SEVERITY:
            errors.append(f"failure_mode severity {sev!r} not in RAF scale {sorted(RAF_SEVERITY)}")

    for er in (data.get("evidence_required") or []):
        lvl = er.get("minimum_evidence_level")
        if lvl and lvl not in RAF_EVIDENCE_LEVELS:
            errors.append(f"evidence_required level {lvl!r} not in RAF scale E0-E5")
        elif lvl in RAF_EVIDENCE_LEVELS_NOT_TEXTUALLY_CONFIRMED:
            warnings.append(
                f"evidence level {lvl} is NOT DEFINED BY RAF textually per rech-deep-audit's own mapping "
                f"doc; used here 'in the spirit of the scale', not as a confirmed RAF level"
            )

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)


def validate_contract_file(path: "str | Path") -> ValidationResult:
    return validate_contract(load_yaml(path))


def template_covers_required_keys(template_path: "str | Path") -> ValidationResult:
    """Defect #5 check: contract_template.yaml must itself contain every key
    in REQUIRED_TOP_LEVEL_KEYS - it is the full approved contract, not a
    partial stub."""
    data = load_yaml(template_path)
    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in data]
    if missing:
        return ValidationResult(valid=False, errors=[f"contract_template.yaml missing key(s): {missing}"])
    return ValidationResult(valid=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args(argv)

    result = validate_contract_file(args.contract)
    if result.valid:
        print("SCHEMA_VALIDATION: PASS")
        for w in result.warnings:
            print(f"  WARNING: {w}")
        return 0
    print("SCHEMA_VALIDATION: FAIL")
    for e in result.errors:
        print(f"  ERROR: {e}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
