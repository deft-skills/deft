"""E1/E3: re-model the spec-kit command library as a DEFT skill family.

1. Split every command body into '## ' sections.
2. Factor the sections that recur, with near-identical text, in several
   commands into ancestor sections. Lines that vary between copies become
   placeholders filled from each command's metadata. Copies that do not fit
   the majority template (drifted clones) override the section, which is
   then a default section instead of a final one.
3. Commands that share a recurring section set get an intermediate
   abstract ancestor (here: the five pipeline phases).
4. Write the DEFT model, check it, resolve every command and compare the
   result with the upstream body (round trip).

Output: speckit-model/ (DEFT library) and results/e1_speckit_refactoring.json
"""
from __future__ import annotations

import collections
import difflib
import glob
import itertools
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import (ROOT, TOKENIZER, UPSTREAM, h2_sections, nonblank, read,  # noqa: E402
                    save, split_frontmatter, tokens)

from deft.check import check_library  # noqa: E402
from deft.loader import load_library  # noqa: E402
from deft.resolve import resolve  # noqa: E402

COMMIT = "b9e08bf3e1a9d82b2a7358e278a6224d54d8783b"
SIMILARITY = 0.8  # mean pairwise similarity of non-blank lines for a recurring section to be factored
OUT = os.path.join(HERE, "speckit-model")


def trim(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return [l.rstrip() for l in lines]


def normalise(text: str) -> list[str]:
    out, blank = [], False
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            blank = True
            continue
        if blank and out:
            out.append("")
        blank = False
        out.append(line)
    return out


def slug(heading: str) -> str:
    return "-".join(heading.lower().replace("-", " ").split())


def load_commands() -> dict:
    cmds = {}
    for f in sorted(glob.glob(os.path.join(UPSTREAM, "spec-kit", "templates", "commands", "*.md"))):
        fm, body = split_frontmatter(read(f))
        meta = yaml.safe_load(fm) or {}
        cmds[os.path.basename(f)[:-3]] = {"meta": meta, "body": body,
                                         "sections": [(h, trim(l)) for h, l in h2_sections(body)]}
    return cmds


def recurring(cmds: dict) -> dict[str, dict[str, list[str]]]:
    by_heading = collections.defaultdict(dict)
    for c, d in cmds.items():
        for h, lines in d["sections"]:
            if h:
                by_heading[h][c] = lines
    factored = {}
    for h, inst in by_heading.items():
        if len(inst) < 2:
            continue
        sims = [difflib.SequenceMatcher(None, [l for l in a if l.strip()], [l for l in b if l.strip()],
                                        autojunk=False).ratio()
                for a, b in itertools.combinations(inst.values(), 2)]
        if sum(sims) / len(sims) >= SIMILARITY:
            factored[h] = inst
    return factored


def template(heading: str, inst: dict[str, list[str]]):
    """Majority template with one slot per varying line."""
    groups = collections.defaultdict(list)
    for c, lines in inst.items():
        groups[len(lines)].append(c)
    size, members = max(groups.items(), key=lambda kv: (len(kv[1]), -kv[0]))
    key = slug(heading).replace("-", "_")
    lines, slots = [], {c: {} for c in members}
    for i in range(size):
        column = {c: inst[c][i] for c in members}
        if len(set(column.values())) == 1:
            lines.append(column[members[0]])
        else:
            name = f"{key}_{i}"
            lines.append("{{meta.%s}}" % name)
            for c, v in column.items():
                slots[c][name] = v
    drifted = sorted(set(inst) - set(members))
    return "\n".join(lines), slots, drifted


def build_model(cmds: dict) -> dict:
    factored = recurring(cmds)
    everywhere = [h for h, inst in factored.items() if len(inst) == len(cmds)]
    partial = [h for h, inst in factored.items() if len(inst) < len(cmds)]
    groups = collections.defaultdict(list)  # recurring-but-partial section set -> commands
    for c, d in cmds.items():
        key = tuple(h for h, _ in d["sections"] if h in partial)
        groups[key].append(c)
    templates = {h: template(h, inst) for h, inst in factored.items()}
    skills, report = [], {"factored_sections": {}}
    for h, (text, slots, drifted) in templates.items():
        report["factored_sections"][h] = {
            "copies": len(factored[h]), "template_lines": nonblank(text.splitlines()),
            "slots": len(next(iter(slots.values()))) if slots else 0, "drifted_copies": drifted}

    def section_for(h):
        text, _, drifted = templates[h]
        return {"name": slug(h), "kind": "default" if drifted else "final", "title": h, "content": text}

    origin = [{"repo": "github/spec-kit", "path": "templates/commands", "commit": COMMIT, "license": "MIT"}]

    def frame(headings, prefix, tail):
        """Factored sections interleaved with empty default sections for the gaps."""
        secs = []
        for i, h in enumerate(headings):
            secs.append({"name": f"{prefix}gap-{i}", "kind": "default", "title": "", "content": ""})
            secs.append(section_for(h))
        secs.append({"name": tail, "kind": "abstract", "title": ""})
        return secs

    skills.append({"name": "speckit-command", "abstract": True, "origin": origin,
                   "description": "Common structure of spec-kit commands.",
                   "sections": frame(everywhere, "", "body")})
    parent_of = {}
    for key, members in sorted(groups.items()):
        if not key:
            for c in members:
                parent_of[c] = ("speckit-command", "speckit-command", ())
            continue
        name = "speckit-with-" + "-and-".join(slug(h) for h in key)
        skills.append({"name": name, "parent": "speckit-command", "abstract": True,
                       "description": f"spec-kit commands with: {', '.join(key)}.",
                       "sections": frame(list(key), f"{name}-", "closing")})
        for c in members:
            parent_of[c] = (name, name, key)

    def split(seq, anchors):
        """Segments of seq before, between and after the anchor headings."""
        names = [h for h, _ in seq]
        pos = [names.index(a) for a in anchors]
        if pos != sorted(pos):
            raise SystemExit(f"anchors out of order in {names}")
        bounds = [-1] + pos + [len(seq)]
        return [seq[bounds[i] + 1:bounds[i + 1]] for i in range(len(bounds) - 1)]

    def text(segment):
        return "\n\n".join(_raw(h, l) for h, l in segment)

    for c, d in cmds.items():
        pname, gname, gkey = parent_of[c]
        refinements, meta = [], {}
        segs = split(d["sections"], everywhere)
        rest = segs[-1]
        for i, seg in enumerate(segs[:-1]):
            if seg:
                refinements.append({"kind": "overrides", "target": f"gap-{i}", "content": text(seg)})
        if gkey:
            gsegs = split(rest, list(gkey))
            body, between, closing = gsegs[0], gsegs[1:-1], gsegs[-1]
            refinements.append({"kind": "implements", "target": "body", "content": text(body)})
            for i, seg in enumerate(between, start=1):
                if seg:
                    refinements.append({"kind": "overrides", "target": f"{gname}-gap-{i}", "content": text(seg)})
            refinements.append({"kind": "implements", "target": "closing", "content": text(closing)})
        else:
            refinements.append({"kind": "implements", "target": "body", "content": text(rest)})
        for h, (_, slots, drifted) in templates.items():
            if c not in factored[h]:
                continue
            if c in drifted:
                refinements.append({"kind": "overrides", "target": slug(h), "content": "\n".join(factored[h][c])})
            else:
                meta.update(slots[c])
        skills.append({"name": c, "parent": pname, "description": d["meta"].get("description", c),
                       "metadata": meta, "refinements": refinements})
    return {"family": "spec-kit", "skills": skills}, report


def _raw(h: str, lines: list[str]) -> str:
    return ("## " + h + "\n\n" if h else "") + "\n".join(lines)


def render_raw(lib, name: str) -> str:
    parts = []
    for s in resolve(lib, name).sections:
        if not s.content.strip() and not s.title:
            continue
        parts.append((f"## {s.title}\n\n" if s.title else "") + s.content)
    return "\n\n".join(parts)


def authored_lines(model: dict) -> int:
    n = 0
    for s in model["skills"]:
        for sec in s.get("sections", []):
            n += nonblank((sec.get("content") or "").splitlines())
        for r in s.get("refinements", []):
            n += nonblank(r["content"].splitlines())
        n += len(s.get("metadata", {}))
    return n


def authored_tokens(model: dict) -> int:
    """Tokens of the authored text: section and refinement content, metadata values."""
    n = 0
    for s in model["skills"]:
        for sec in s.get("sections", []):
            n += tokens(sec.get("content") or "")
        for r in s.get("refinements", []):
            n += tokens(r["content"])
        n += sum(tokens(str(v)) for v in s.get("metadata", {}).values())
    return n


class _Dumper(yaml.SafeDumper):
    """Write multi-line strings as literal blocks."""


def _str(dumper, value):
    if "\n" in value:
        value = "\n".join(l.rstrip() for l in value.splitlines())  # literal blocks forbid trailing spaces
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", value)


_Dumper.add_representer(str, _str)


def main() -> dict:
    cmds = load_commands()
    model, report = build_model(cmds)
    os.makedirs(os.path.join(OUT, "skills"), exist_ok=True)
    with open(os.path.join(OUT, "library.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Generated by refactor_speckit.py from spec-kit (MIT); do not edit.\n")
        yaml.safe_dump({"name": "spec-kit-in-deft",
                        "licenses": {"github/spec-kit": "../../../upstream/spec-kit/LICENSE"}}, fh, sort_keys=False)
    with open(os.path.join(OUT, "skills", "spec-kit.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Generated by refactor_speckit.py from spec-kit (MIT); do not edit.\n")
        yaml.dump(model, fh, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=120)
    lib = load_library(OUT)
    violations = [str(v) for v in check_library(lib)]
    identical, diffs = [], {}
    for c, d in cmds.items():
        a, b = normalise(d["body"]), normalise(render_raw(lib, c))
        if a == b:
            identical.append(c)
        else:
            diffs[c] = list(difflib.unified_diff(a, b, lineterm="", n=0))[:20]
    upstream_lines = sum(nonblank(d["body"].splitlines()) for d in cmds.values())
    authored = authored_lines(model)
    upstream_tok = sum(tokens(d["body"]) for d in cmds.values())
    authored_tok = authored_tokens(model)
    result = {
        "commands": len(cmds),
        "upstream_nonblank_lines": upstream_lines,
        "deft_authored_lines": authored,
        "reduction": round(1 - authored / upstream_lines, 3),
        "tokenizer": TOKENIZER,
        "upstream_tokens": upstream_tok,
        "deft_authored_tokens": authored_tok,
        "token_reduction": round(1 - authored_tok / upstream_tok, 3),
        "violations": violations,
        "round_trip_identical": len(identical),
        "round_trip_diffs": diffs,
        "hierarchy": {s["name"]: s.get("parent") for s in model["skills"]},
        **report,
    }
    save("e1_speckit_refactoring.json", result)
    return result


if __name__ == "__main__":
    r = main()
    print({k: v for k, v in r.items() if k not in ("round_trip_diffs", "hierarchy")})
    for c, d in r["round_trip_diffs"].items():
        print("DIFF", c)
        print("\n".join(d))
