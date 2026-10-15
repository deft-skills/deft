"""E1 (expressiveness): structuring conventions in two public skill libraries.

Scans the pinned copies under upstream/ and counts, per library, the
conventions practitioners use to relate skills, together with the DEFT
construct that represents each one (see mapping.yaml).

Output: results/e1_survey.json
"""
from __future__ import annotations

import collections
import glob
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import UPSTREAM, h2_sections, nonblank, read, save, split_frontmatter  # noqa: E402


def speckit() -> dict:
    files = sorted(glob.glob(os.path.join(UPSTREAM, "spec-kit", "templates", "commands", "*.md")))
    commands = {}
    for f in files:
        fm, body = split_frontmatter(read(f))
        meta = yaml.safe_load(fm) or {}
        commands[os.path.basename(f)[:-3]] = (meta, h2_sections(body), body)
    heading_count = collections.Counter(h for _, secs, _ in commands.values() for h, _ in secs)
    shared = {h: n for h, n in heading_count.items() if n >= 2}
    handoffs = [(c, h["agent"]) for c, (m, _, _) in commands.items() for h in m.get("handoffs", []) or []]
    scripts = [c for c, (m, _, _) in commands.items() if m.get("scripts")]
    done_when = [c for c, (_, secs, _) in commands.items() if any(h == "Done When" for h, _ in secs)]
    total_lines = sum(nonblank(b.splitlines()) for _, _, b in commands.values())
    # lines of the sections shared by two or more commands
    shared_lines = sum(nonblank(lines) for _, secs, _ in commands.values()
                       for h, lines in secs if h in shared)
    return {
        "library": "github/spec-kit",
        "skills": len(commands),
        "nonblank_lines": total_lines,
        "shared_headings": dict(sorted(shared.items(), key=lambda kv: -kv[1])),
        "lines_under_shared_headings": shared_lines,
        "handoff_edges": len(handoffs),
        "handoffs": sorted(set(f"{a} -> {b}" for a, b in handoffs)),
        "skills_with_scripts": len(scripts),
        "skills_with_done_when": len(done_when),
        "skills_with_pre_execution_checks": sum(
            1 for _, secs, _ in commands.values() if any(h == "Pre-Execution Checks" for h, _ in secs)),
    }


REF = re.compile(r"superpowers:([a-z][a-z0-9-]+)")
REQUIRED = re.compile(r"REQUIRED SUB-SKILL[^\n]*?superpowers:([a-z][a-z0-9-]+)")


def superpowers() -> dict:
    files = sorted(glob.glob(os.path.join(UPSTREAM, "superpowers", "skills", "*", "SKILL.md")))
    names = [os.path.basename(os.path.dirname(f)) for f in files]
    refs, required, graphs, lines = set(), set(), 0, 0
    for f, n in zip(files, names):
        text = read(f)
        _, body = split_frontmatter(text)
        lines += nonblank(body.splitlines())
        refs |= {(n, m) for m in REF.findall(text) if m != n}
        required |= {(n, m) for m in REQUIRED.findall(text) if m != n}
        graphs += len(re.findall(r"```dot", text))
    return {
        "library": "obra/superpowers",
        "skills": len(names),
        "nonblank_lines": lines,
        "prose_reference_edges": len(refs),
        "skills_referencing_others": len({a for a, _ in refs}),
        "required_subskill_edges": len(required),
        "embedded_dot_graphs": graphs,
        "skills_with_dot_graphs": sum(1 for f in files if "```dot" in read(f)),
        "reference_edges": sorted(f"{a} -> {b}" for a, b in refs),
        # writing-plans hands over to one of two executors chosen at run time
        "alternative_executors": ["executing-plans", "subagent-driven-development"],
    }


def main() -> dict:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "mapping.yaml"), encoding="utf-8") as fh:
        mapping = yaml.safe_load(fh)
    result = {"spec-kit": speckit(), "superpowers": superpowers(), "mapping": mapping["conventions"]}
    covered = sum(1 for c in mapping["conventions"] if c["coverage"] == "full")
    partial = sum(1 for c in mapping["conventions"] if c["coverage"] == "partial")
    result["coverage"] = {"conventions": len(mapping["conventions"]), "full": covered, "partial": partial,
                          "none": len(mapping["conventions"]) - covered - partial}
    save("e1_survey.json", result)
    return result


if __name__ == "__main__":
    r = main()
    for lib in ("spec-kit", "superpowers"):
        print(lib, {k: v for k, v in r[lib].items() if not isinstance(v, (list, dict))})
    print("coverage", r["coverage"])
