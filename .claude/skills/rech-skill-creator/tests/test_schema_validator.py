from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from schema_validator import (  # noqa: E402
    REQUIRED_TOP_LEVEL_KEYS,
    template_covers_required_keys,
    validate_contract,
    validate_contract_file,
)

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "contract_template.yaml"


def test_contract_template_matches_required_key_set():
    """Defect #5: contract_template.yaml must contain every required
    top-level key - it is the full approved contract, not a partial stub."""
    result = template_covers_required_keys(TEMPLATE_PATH)
    assert result.valid, result.errors


def test_metadata_field_accepted():
    """Defect #9: the schema must accept a populated `metadata` field."""
    data = {k: [] for k in REQUIRED_TOP_LEVEL_KEYS}
    data["metadata"] = {"owner": "someone", "status": "draft", "tags": ["x"]}
    result = validate_contract(data)
    assert not any("metadata" in e for e in result.errors)


def test_metadata_missing_is_rejected():
    data = {k: [] for k in REQUIRED_TOP_LEVEL_KEYS if k != "metadata"}
    result = validate_contract(data)
    assert not result.valid
    assert any("metadata" in e for e in result.errors)


def test_metadata_wrong_type_is_rejected():
    data = {k: [] for k in REQUIRED_TOP_LEVEL_KEYS}
    data["metadata"] = "not a mapping"
    result = validate_contract(data)
    assert not result.valid
    assert any("metadata must be a mapping" in e for e in result.errors)


def test_severity_must_be_raf_scale():
    data = {k: [] for k in REQUIRED_TOP_LEVEL_KEYS}
    data["metadata"] = {}
    data["invariants"] = [{"id": "INV-X-Y-1", "severity": "SUPER_URGENT"}]
    result = validate_contract(data)
    assert not result.valid
    assert any("RAF scale" in e for e in result.errors)


def test_evidence_level_e0_e5_warns_but_does_not_fail():
    data = {k: [] for k in REQUIRED_TOP_LEVEL_KEYS}
    data["metadata"] = {}
    data["evidence_required"] = [{"field": "x", "minimum_evidence_level": "E0"}]
    result = validate_contract(data)
    assert result.valid
    assert any("NOT DEFINED BY RAF" in w for w in result.warnings)


def test_fixture_contract_is_valid():
    fixture = Path(__file__).resolve().parent / "fixtures" / "minimal_skill_pkg" / "contract.yaml"
    result = validate_contract_file(fixture)
    assert result.valid, result.errors
