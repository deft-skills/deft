"""Command-line interface: python -m deft <command> ..."""
from __future__ import annotations

import argparse
import json
import sys

from .check import check_library, obligations
from .generate import generate, render_skill, render_workflow
from .loader import ModelError, load_library
from .model import CompositeSkill


def _load(path):
    try:
        return load_library(path)
    except ModelError as exc:
        print(f"model error: {exc}", file=sys.stderr)
        raise SystemExit(2)


def cmd_check(a) -> int:
    lib = _load(a.library)
    violations = check_library(lib)
    if a.json:
        print(json.dumps([v.__dict__ for v in violations], indent=2))
    else:
        for v in violations:
            print(v)
        print(f"{len(lib.types)} types, {len(lib.skills)} skills: "
              f"{len(violations)} violation(s)")
    return 1 if violations else 0


def cmd_resolve(a) -> int:
    lib = _load(a.library)
    sk = lib.skills.get(a.skill)
    if sk is None:
        print(f"unknown skill '{a.skill}'", file=sys.stderr)
        return 2
    text = render_workflow(lib, sk) if isinstance(sk, CompositeSkill) else render_skill(lib, a.skill)
    sys.stdout.write(text)
    return 0


def cmd_generate(a) -> int:
    lib = _load(a.library)
    violations = check_library(lib)
    if violations and not a.force:
        for v in violations:
            print(v, file=sys.stderr)
        print("refusing to generate from an ill-formed library (use --force)", file=sys.stderr)
        return 1
    names = generate(lib, a.out, provenance=not a.no_provenance)
    print(f"generated {len(names)} skill(s) into {a.out}")
    return 0


def cmd_obligations(a) -> int:
    lib = _load(a.library)
    for sk in lib.skills.values():
        if isinstance(sk, CompositeSkill) and (a.workflow in (None, sk.name)):
            for o in obligations(lib, sk):
                print(f"## {sk.name}: {o.edge}")
                print("guarantees:")
                for c in o.post or ["(none)"]:
                    print(f"  - {c}")
                print("must entail:")
                for c in o.pre:
                    print(f"  - {c}")
                print()
    return 0


def cmd_diagram(a) -> int:
    from .diagram import plantuml_library, plantuml_workflow
    lib = _load(a.library)
    if a.workflow:
        sys.stdout.write(plantuml_workflow(lib, lib.skills[a.workflow]))
    else:
        sys.stdout.write(plantuml_library(lib))
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="deft", description="DEFT skill library tools")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check S and C constraints")
    c.add_argument("library")
    c.add_argument("--json", action="store_true")
    c.set_defaults(fn=cmd_check)
    r = sub.add_parser("resolve", help="print the resolved SKILL.md of one skill")
    r.add_argument("library")
    r.add_argument("skill")
    r.set_defaults(fn=cmd_resolve)
    g = sub.add_parser("generate", help="write one SKILL.md per concrete skill")
    g.add_argument("library")
    g.add_argument("--out", default="skills")
    g.add_argument("--force", action="store_true")
    g.add_argument("--no-provenance", action="store_true")
    g.set_defaults(fn=cmd_generate)
    o = sub.add_parser("obligations", help="list C5 contract obligations for review")
    o.add_argument("library")
    o.add_argument("--workflow")
    o.set_defaults(fn=cmd_obligations)
    d = sub.add_parser("diagram", help="PlantUML class diagram of a library or workflow")
    d.add_argument("library")
    d.add_argument("--workflow")
    d.set_defaults(fn=cmd_diagram)
    a = p.parse_args(argv)
    return a.fn(a)
