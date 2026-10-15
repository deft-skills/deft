"""Inspect a finished run of deliver-feature against what the workflow prescribes.

    python examples/account-service/check_run.py ../deft-run [--json report.json]

Reports the artifacts the skills ask for (requirements, plan, ledger, tests),
the traceability from requirement ids to tests, the work on a feature branch,
and the verdict of the test suite run with the run's own virtual environment.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys

IDS = re.compile(r"\b(US-\d+|FR-\d+|QR-\d+)\b")


def files(root, pattern):
    return sorted(f for f in glob.glob(os.path.join(root, pattern), recursive=True)
                  if os.sep + ".venv" + os.sep not in f and os.path.isfile(f))


def python_of(run: str) -> str:
    for candidate in (os.path.join(run, ".venv", "Scripts", "python.exe"),
                      os.path.join(run, ".venv", "bin", "python")):
        if os.path.exists(candidate):
            return candidate
    return sys.executable


def git(run: str, *args) -> str:
    return subprocess.run(["git", *args], cwd=run, capture_output=True, text=True).stdout.strip()


def main(run: str) -> dict:
    spec = files(run, "specs/**/requirements.md")
    plan = files(run, "specs/**/plan.md")
    ledger = files(run, "**/progress.md")
    tests = [f for f in files(run, "tests/**/*") if f.endswith((".py", ".feature"))]
    req_ids = set()
    for f in spec:
        with open(f, encoding="utf-8") as fh:
            req_ids |= set(IDS.findall(fh.read()))
    matrix = {r: [] for r in sorted(req_ids)}
    for f in tests:
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for r in sorted(set(IDS.findall(fh.read()))):
                matrix.setdefault(r, []).append(os.path.relpath(f, run))
    # commits made on top of the branch the run started from (main or master)
    base = next((b for b in ("main", "master") if git(run, "rev-parse", "--verify", "-q", b)), None)
    head = git(run, "rev-parse", "--abbrev-ref", "HEAD")
    if base and base != head:
        commits = git(run, "rev-list", f"{base}..HEAD").splitlines()
    else:
        commits = git(run, "log", "--oneline").splitlines()[1:]
    suite = subprocess.run([python_of(run), "-m", "pytest", "-q"], cwd=run, capture_output=True, text=True)
    report = {
        "artifacts": {"requirements": [os.path.relpath(f, run) for f in spec],
                      "plan": [os.path.relpath(f, run) for f in plan],
                      "ledger": [os.path.relpath(f, run) for f in ledger],
                      "test_files": [os.path.relpath(f, run) for f in tests]},
        "requirements": sorted(req_ids),
        "traceability": matrix,
        "untested_requirements": [r for r, t in matrix.items() if not t],
        "branch": git(run, "rev-parse", "--abbrev-ref", "HEAD"),
        "commits_after_baseline": len(commits),
        "suite_exit_code": suite.returncode,
        "suite_summary": (suite.stdout.strip().splitlines() or [""])[-1],
    }
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--json", help="also write the report to this file")
    a = ap.parse_args()
    r = main(a.run)
    print(json.dumps(r, indent=2))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=2)
