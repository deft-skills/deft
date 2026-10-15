"""Prepare a run of the deliver-feature workflow with a coding agent.

Copies this example system to a new folder, generates the DEFT skills into the
skills folder your agent reads, makes a first commit, and prints the next steps.

    python examples/account-service/prepare.py --dest ../deft-run
    python examples/account-service/prepare.py --dest ../deft-run --skills-dir .agents/skills
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from deft.check import check_library  # noqa: E402
from deft.generate import generate  # noqa: E402
from deft.loader import load_library  # noqa: E402

TOOLING = ("prepare.py", "check_run.py", "README.md", "__pycache__", ".pytest_cache")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", required=True, help="folder of the new run (must not exist)")
    ap.add_argument("--skills-dir", default=".claude/skills",
                    help="skills folder of your agent, relative to the run folder (default: .claude/skills)")
    ap.add_argument("--models", default=os.path.join(ROOT, "models"), help="DEFT library to generate from")
    a = ap.parse_args()
    if os.path.exists(a.dest):
        raise SystemExit(f"{a.dest} already exists")
    lib = load_library(a.models)
    violations = check_library(lib)
    if violations:
        for v in violations:
            print(v, file=sys.stderr)
        raise SystemExit("the library has violations; fix them before generating")
    shutil.copytree(HERE, a.dest, ignore=shutil.ignore_patterns(*TOOLING))
    names = generate(lib, os.path.join(a.dest, a.skills_dir))
    git = ["git", "-c", "user.name=run", "-c", "user.email=run@example.org", "-c", "core.autocrlf=false"]
    subprocess.run(["git", "init", "-q"], cwd=a.dest, check=True)
    subprocess.run(git + ["add", "-A"], cwd=a.dest, check=True)
    subprocess.run(git + ["commit", "-qm", "Existing system"], cwd=a.dest, check=True)
    dest = os.path.abspath(a.dest)
    print(f"Prepared {dest}")
    print(f"  {len(names)} skills in {a.skills_dir}/: {', '.join(names)}")
    print("\nNext steps:")
    print(f"  1. cd {dest}")
    print("  2. python -m venv .venv  and install:  pip install -r requirements.txt")
    print("  3. python -m pytest      (3 tests pass: the existing system)")
    print("  4. start your coding agent in this folder and give it the prompt in FEATURE-REQUEST.md")
    print(f"  5. python {os.path.join(HERE, 'check_run.py')} {dest}")


if __name__ == "__main__":
    main()
