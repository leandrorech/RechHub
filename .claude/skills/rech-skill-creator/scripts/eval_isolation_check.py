#!/usr/bin/env python3
"""eval_isolation_check.py - mandatory pre-check, run BEFORE snapshot/run
(defect #7: never PASS just because --scope was omitted).

"Scope" = an explicit set of eval_ids this isolation check is claiming to
guarantee non-interference for (no shared temp dirs, env vars, or config
files clobbering each other across evals in that set), supplied via
`--scope EVAL-A,EVAL-B` or `--scope-file scope.yaml` (a YAML list of eval_ids).

Status vocabulary (rsc_common.IsolationStatus), same family used by
skills_api_validate.py for consistency:

  PASS            - scope explicit, non-empty, covers every `required` eval
                    in the manifest, and no shared-resource overlap detected.
  PARTIAL         - scope resolved to a real, non-empty set, but it covers
                    only part of the required evals, OR an overlap was found.
  UNVERIFIED      - --scope/--scope-file was omitted entirely, or resolved to
                    zero evals. Isolation cannot be confirmed either way.

`auto/infer = diagnostic only`: if scope is omitted, this script MAY compute a
suggested scope (e.g. via a naive heuristic over declared eval inputs) and
attach it to the UNVERIFIED result as a hint - but that inferred suggestion is
never substituted for the explicit value and never flips the status to PASS.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import IsolationStatus, load_yaml  # noqa: E402


def _resolve_scope(scope: str | None, scope_file: str | None, manifest: dict) -> list:
    if scope:
        return [s.strip() for s in scope.split(",") if s.strip()]
    if scope_file:
        data = load_yaml(scope_file)
        if isinstance(data, list):
            return list(data)
        return []
    return []


def _suggest_scope(manifest: dict) -> list:
    """Diagnostic-only heuristic: suggest every declared eval_id as a starting
    point. Never used to satisfy the PASS condition - see module docstring."""
    return [e["eval_id"] for e in manifest.get("evals", [])]


def _detect_shared_resource_overlap(scoped_ids: list, manifest: dict) -> list:
    """Best-effort static overlap check: flags evals in scope that declare an
    identical, non-empty `input.shared_resource` value (e.g. two evals both
    writing to the same fixture path). Absence of a declared shared_resource
    is not proof of isolation - only a detected overlap is reported here."""
    by_resource: dict = {}
    for e in manifest.get("evals", []):
        if e["eval_id"] not in scoped_ids:
            continue
        resource = (e.get("input") or {}).get("shared_resource")
        if resource:
            by_resource.setdefault(resource, []).append(e["eval_id"])
    return [
        {"resource": resource, "eval_ids": ids}
        for resource, ids in by_resource.items()
        if len(ids) > 1
    ]


def eval_isolation_check(manifest_path: "str | Path", scope: str | None = None, scope_file: str | None = None) -> dict:
    manifest = load_yaml(manifest_path)
    required_ids = {e["eval_id"] for e in manifest.get("evals", []) if e.get("required", True)}

    scoped_ids = _resolve_scope(scope, scope_file, manifest)

    if not scoped_ids:
        return {
            "status": IsolationStatus.UNVERIFIED.value,
            "reason": "--scope/--scope-file omitted or resolved to zero evals; isolation cannot be confirmed",
            "suggested_scope_diagnostic_only": _suggest_scope(manifest),
        }

    scoped_set = set(scoped_ids)
    overlaps = _detect_shared_resource_overlap(scoped_ids, manifest)
    if overlaps:
        return {
            "status": IsolationStatus.PARTIAL.value,
            "reason": f"shared-resource overlap detected within scope: {overlaps}",
            "scope": sorted(scoped_set),
        }

    if scoped_set != required_ids:
        return {
            "status": IsolationStatus.PARTIAL.value,
            "reason": "scope does not cover every required eval "
                      f"(missing: {sorted(required_ids - scoped_set)})",
            "scope": sorted(scoped_set),
            "required": sorted(required_ids),
        }

    return {
        "status": IsolationStatus.PASS.value,
        "reason": "explicit scope, full coverage of required evals, no overlap detected",
        "scope": sorted(scoped_set),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--scope", help="Comma-separated eval_ids")
    parser.add_argument("--scope-file", help="YAML file containing a list of eval_ids")
    args = parser.parse_args(argv)

    result = eval_isolation_check(args.manifest, scope=args.scope, scope_file=args.scope_file)
    print(f"EVAL_ISOLATION: {result['status']} - {result['reason']}")
    return 0 if result["status"] == IsolationStatus.PASS.value else 1


if __name__ == "__main__":
    raise SystemExit(main())
