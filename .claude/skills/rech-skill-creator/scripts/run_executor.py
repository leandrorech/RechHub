#!/usr/bin/env python3
"""run_executor.py - the harness/wrapper/adapter that executes declared evals
from the FROZEN manifest copy against a candidate skill.

Refuses to run at all if snapshot_manager.py has not frozen the manifest
first (structural enforcement of defects #1/#8: a run cannot see a manifest
that was never snapshotted, because this module only ever opens the frozen
copy under `<workdir>/snapshot/eval_manifest.canonical.yaml`).

Each declared eval resolves to exactly one of three outcomes, written per-eval
under `<runs_dir>/<run_id>/<eval_id>/result.json`:

  PASS         - executed, all assertions satisfied.
  FAIL         - executed, at least one assertion failed.
  RUN_INVALID  - could not be meaningfully executed at all (timeout, infra
                 exception, or an execution_mode this offline harness cannot
                 perform, e.g. claude_invocation/manual_required). This is a
                 THIRD bucket: never counted as PASS, never counted as a
                 functional FAIL either (see valid_run_gate.py).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rsc_common import RunOutcome, load_yaml, now_iso, read_json, write_json  # noqa: E402
from snapshot_manager import (  # noqa: E402
    canonical_manifest_path,
    decision_input_manifest_path,
    is_frozen,
)

NON_EXECUTABLE_MODES = {"claude_invocation", "manual_required"}


def _evaluate_assertions(assertions: list, stdout: str, stderr: str, exit_code: int) -> bool:
    targets = {"stdout": stdout, "stderr": stderr}
    for a in assertions:
        kind = a.get("type")
        target_text = targets.get(a.get("target", "stdout"), "")
        expected = a.get("expected")
        if kind == "exit_code":
            if exit_code != expected:
                return False
        elif kind == "contains":
            if str(expected) not in target_text:
                return False
        elif kind == "regex":
            if not re.search(str(expected), target_text):
                return False
        elif kind == "exact":
            if target_text.strip() != str(expected).strip():
                return False
        else:
            # Unknown assertion type: conservatively FAIL rather than silently
            # pass an assertion this harness doesn't understand.
            return False
    return True


def _run_one_eval(eval_entry: dict, cwd: "str | Path") -> tuple:
    mode = eval_entry.get("execution_mode")
    if mode in NON_EXECUTABLE_MODES:
        return RunOutcome.RUN_INVALID, {
            "reason": f"execution_mode={mode} cannot be executed by this offline harness"
        }
    if mode != "cli_subprocess":
        return RunOutcome.RUN_INVALID, {"reason": f"unknown execution_mode={mode!r}"}

    cmd = (eval_entry.get("input") or {}).get("cmd")
    if not cmd:
        return RunOutcome.RUN_INVALID, {"reason": "cli_subprocess eval missing input.cmd"}

    timeout = eval_entry.get("timeout_seconds", 60)
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return RunOutcome.RUN_INVALID, {"reason": f"timeout after {timeout}s"}
    except OSError as exc:
        return RunOutcome.RUN_INVALID, {"reason": f"infra exception: {exc}"}

    ok = _evaluate_assertions(
        eval_entry.get("assertions", []), proc.stdout, proc.stderr, proc.returncode
    )
    details = {
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }
    return (RunOutcome.PASS if ok else RunOutcome.FAIL), details


def execute_run(workdir: "str | Path", run_id: str, runs_dir: "str | Path" = None, cwd: "str | Path" = None) -> dict:
    workdir = Path(workdir)
    if not is_frozen(workdir):
        raise RuntimeError(
            "EVAL_MANIFEST not frozen: run snapshot_manager.py freeze before run_executor.py "
            "(no run may execute against an unfrozen manifest)"
        )

    manifest = load_yaml(canonical_manifest_path(workdir))
    decision_input_manifest = read_json(decision_input_manifest_path(workdir))
    manifest_sha256 = decision_input_manifest["manifest_sha256"]
    manifest_id = decision_input_manifest["manifest_id"]

    runs_dir = Path(runs_dir) if runs_dir else workdir / "runs"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    exec_cwd = Path(cwd) if cwd else workdir

    per_eval = {}
    for eval_entry in manifest.get("evals", []):
        eval_id = eval_entry["eval_id"]
        outcome, details = _run_one_eval(eval_entry, exec_cwd)
        eval_dir = run_dir / eval_id
        eval_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "eval_id": eval_id,
            "outcome": outcome.value,
            "manifest_sha256": manifest_sha256,
            "executed_at": now_iso(),
            "details": details,
        }
        write_json(eval_dir / "result.json", result)
        per_eval[eval_id] = result

    run_meta = {
        "run_id": run_id,
        "manifest_sha256": manifest_sha256,
        "manifest_id": manifest_id,
        "created_at": now_iso(),
        "eval_ids": list(per_eval.keys()),
    }
    write_json(run_dir / "run_meta.json", run_meta)
    return {"run_meta": run_meta, "evals": per_eval}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--runs-dir")
    parser.add_argument("--cwd", help="Directory evals are executed from (default: workdir)")
    args = parser.parse_args(argv)

    try:
        execute_run(args.workdir, args.run_id, runs_dir=args.runs_dir, cwd=args.cwd)
    except RuntimeError as exc:
        print(f"RUN EXECUTOR REFUSED: {exc}", file=sys.stderr)
        return 1
    print(f"RUN {args.run_id} COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
