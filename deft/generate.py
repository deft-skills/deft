"""Model-to-text transformation: one SKILL.md per concrete skill.

Abstract skills are not generated: their content reaches agents through the
resolved concrete descendants. Composite skills are generated as workflow
skills whose steps name the skills that perform them.
"""
from __future__ import annotations

import os
import shutil

import yaml

from . import __version__
from .check import is_executable
from .model import (MANY, CompositeSkill, ControlEdgeKind, ControlKind,
                    ControlNode, Direction, Library, Parameter, SkillNode)
from .resolve import effective_metadata, provenance_trail, resolve, substitute

LICENSE_ID = "GPL-3.0-only"


def _mult(p: Parameter) -> str:
    up = "*" if p.upper == MANY else str(p.upper)
    return str(p.lower) if str(p.lower) == up else f"{p.lower}..{up}"


def _words(lower: int, upper: int) -> str:
    if upper == MANY:
        return "one or more" if lower == 1 else ("any number" if lower == 0 else f"{lower} or more")
    if lower == upper:
        return "one" if lower == 1 else str(lower)
    if lower == 0 and upper == 1:
        return "optional"
    return f"{lower} to {upper}"


def _sig(p: Parameter) -> str:
    return f"{p.name}: {p.type} [{_mult(p)}]"


def _origin_line(lib: Library, name: str) -> str:
    origins = []
    for s in lib.skill_ancestors(name):
        for o in lib.skills[s].origin:
            entry = f"{o.repo}@{o.commit[:7]} {o.path} ({o.license}, {o.mode.value})"
            if entry not in origins:
                origins.append(entry)
    return "; ".join(origins)


def upstream_licenses(lib: Library, name: str) -> dict[str, str]:
    """Published file name -> source path of every upstream licence."""
    files = {}
    for s in lib.skill_ancestors(name):
        for o in lib.skills[s].origin:
            src = lib.license_files.get(o.repo)
            if src:
                files[f"LICENSE-{o.repo.split('/')[-1]}.txt"] = src
    return files


def _frontmatter(lib: Library, name: str, description: str, extra: dict) -> str:
    meta = {"deft-version": __version__,
            "deft-lineage": " > ".join(reversed(lib.skill_ancestors(name)))}
    params = lib.effective_params(name)
    ins = [_sig(p) for p in params.values() if p.direction == Direction.IN]
    outs = [_sig(p) for p in params.values() if p.direction == Direction.OUT]
    updates = [_sig(p) for p in params.values() if p.direction == Direction.INOUT]
    if ins:
        meta["deft-inputs"] = "; ".join(ins)
    if outs:
        meta["deft-outputs"] = "; ".join(outs)
    if updates:
        meta["deft-updates"] = "; ".join(updates)
    origin = _origin_line(lib, name)
    if origin:
        meta["deft-origin"] = origin
    meta.update(extra)
    lic = lib.effective_attribute(name, "license") or LICENSE_ID
    if upstream_licenses(lib, name):
        lic += " (includes third-party material; see LICENSE-*.txt)"
    fm = {"name": name, "description": description, "license": lic}
    compatibility = lib.effective_attribute(name, "compatibility")
    if compatibility:
        fm["compatibility"] = compatibility
    fm["metadata"] = meta
    tools = lib.effective_attribute(name, "allowed_tools")
    if tools:
        fm["allowed-tools"] = tools
    return "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000) + "---\n"


def _artifact_lines(lib: Library, type_name: str) -> list[str]:
    lines = []
    for p in lib.effective_properties(type_name):
        mult = "required" if (p.lower, p.upper) == (1, 1) else _words(p.lower, p.upper)
        vals = f"; one of {', '.join(p.values)}" if p.values else ""
        desc = f": {p.description}" if p.description else ""
        lines.append(f"  - `{p.name}` ({mult}{vals}){desc}")
    return lines


def _io_section(lib: Library, name: str) -> str:
    params = lib.effective_params(name)
    out = ["## Inputs and outputs", ""]
    for direction, label in ((Direction.IN, "Input"), (Direction.INOUT, "Updated in place"),
                             (Direction.OUT, "Output")):
        for p in params.values():
            if p.direction != direction:
                continue
            desc = f". {p.description[0].upper()}{p.description[1:]}." if p.description else ""
            t = lib.types.get(p.type)
            out.append(f"- {label} `{p.name}`: {p.type} ({_words(p.lower, p.upper)}){desc}")
            if t is not None and t.description:
                out.append(f"  {t.description}")
            out += _artifact_lines(lib, p.type)
    return "\n".join(out)


def _conditions(title: str, conds: list[str]) -> str:
    if not conds:
        return ""
    return f"## {title}\n\n" + "\n".join(f"- {c}" for c in conds)


def render_skill(lib: Library, name: str, provenance: bool = True) -> str:
    r = resolve(lib, name)
    pre, post = lib.effective_conditions(name)
    meta = effective_metadata(lib, name)
    pre = [substitute(c, name, meta) for c in pre]
    post = [substitute(c, name, meta) for c in post]
    parts = [_frontmatter(lib, name, r.description, {}), f"# {meta.get('title', name)}", ""]
    parts.append(_io_section(lib, name))
    if pre:
        parts += ["", _conditions("Before you start", pre)]
    for sec in r.sections:
        parts += ["", f"## {sec.title or sec.name}"]
        if provenance:
            trail = provenance_trail(sec)
            parts.append(f"<!-- deft: {sec.kind.value} section '{sec.name}'; {trail} -->")
        parts += ["", sec.content]
    if post:
        parts += ["", _conditions("Done when", post)]
    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------- workflows

def topological_steps(comp: CompositeSkill) -> list[str]:
    """Node order induced by data, sequence and invokes edges (Kahn)."""
    ids = [n.name for n in comp.nodes]
    succ = {n: [] for n in ids}
    indeg = {n: 0 for n in ids}
    edges = set()
    for e in comp.data:
        if e.source.node in succ and e.target.node in succ:
            edges.add((e.source.node, e.target.node))
    for c in comp.control:
        if c.kind != ControlEdgeKind.REPAIR and c.source in succ and c.target in succ:
            edges.add((c.source, c.target))
    for a, b in sorted(edges):
        succ[a].append(b)
        indeg[b] += 1
    ready = [n for n in ids if indeg[n] == 0]
    order = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for m in succ[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
    return order


def render_workflow(lib: Library, comp: CompositeSkill, provenance: bool = True) -> str:
    invoked = {c.target: c.source for c in comp.control if c.kind == ControlEdgeKind.INVOKES}
    requires = sorted({n.effective for n in comp.skill_nodes()})
    fm = _frontmatter(lib, comp.name, comp.description, {"deft-requires": ", ".join(requires)})
    meta = effective_metadata(lib, comp.name)
    parts = [fm, f"# {meta.get('title', comp.name)}", ""]
    parts.append("This skill coordinates other skills. Load each named skill when its step starts, "
                 "and pass the artifacts exactly as listed. Each step is ready when all its inputs exist; "
                 "steps with no dependency between them may run in any order.")
    parts += ["", _io_section(lib, comp.name)]
    if comp.pre:
        parts += ["", _conditions("Before you start", comp.pre)]
    parts += ["", "## Workflow", ""]
    order = [n for n in topological_steps(comp) if n not in invoked]
    step_no = {n: i + 1 for i, n in enumerate(order)}
    incoming = {}
    for e in comp.data:
        incoming.setdefault(e.target.node, []).append(e)
    for nid in order:
        node = comp.node(nid)
        if isinstance(node, SkillNode):
            sk = lib.skills[node.effective]
            role = f" (role: {node.role})" if node.bind else ""
            parts.append(f"### Step {step_no[nid]}: {nid}")
            parts.append("")
            parts.append(f"Use the skill `{node.effective}`{role}.")
            for e in incoming.get(nid, []):
                if e.source.node == "self":
                    parts.append(f"- Input `{e.target.param}`: the workflow input `{e.source.param}`.")
                else:
                    parts.append(f"- Input `{e.target.param}`: the `{e.source.param}` of step "
                                 f"{step_no.get(e.source.node, '?')} ({e.source.node}).")
            outs = [p for p in lib.effective_params(sk.name).values() if p.direction.is_output]
            for p in outs:
                parts.append(f"- Output `{p.name}`: {p.type}.")
            for callee, caller in invoked.items():
                if caller == nid:
                    cn = comp.node(callee)
                    parts.append(f"- While you perform this step, invoke the skill `{cn.effective}` "
                                 f"for each unit of work, and follow it completely.")
            for c in comp.control:
                if c.kind == ControlEdgeKind.REPAIR and c.target == nid:
                    payload = f" with the `{c.carries.source.param}` from {c.source}" if c.carries else ""
                    parts.append(f"- When the workflow returns here after a failure{payload}, "
                                 f"fix only what the diagnosis identifies.")
            parts.append("")
        elif isinstance(node, ControlNode) and node.kind == ControlKind.DECISION:
            parts.append(f"### Step {step_no[nid]}: {nid} (decision)")
            parts.append("")
            for c in comp.control:
                if c.source == nid:
                    dest = "finish the workflow" if isinstance(comp.node(c.target), ControlNode) and \
                        comp.node(c.target).kind == ControlKind.FINAL else f"go to step {step_no.get(c.target, '?')} ({c.target})"
                    parts.append(f"- If {c.guard}: {dest}.")
            parts.append("")
    repairs = [c for c in comp.control if c.kind == ControlEdgeKind.REPAIR]
    if repairs:
        parts.append("### Repair loop")
        parts.append("")
        for c in repairs:
            parts.append(f"- After step {step_no.get(c.source, '?')} ({c.source}), return to step "
                         f"{step_no.get(c.target, '?')} ({c.target}) and continue from there. "
                         f"Do this at most {c.bound} times. If the limit is reached, stop and report "
                         f"the open failures instead of continuing.")
        parts.append("")
    if comp.post:
        parts += [_conditions("Done when", comp.post)]
    return "\n".join(parts).rstrip() + "\n"


def mermaid(lib: Library, comp: CompositeSkill) -> str:
    lines = ["flowchart TB", "  in((start))"]
    for n in comp.nodes:
        if isinstance(n, SkillNode):
            label = f"{n.role}<br/><b>{n.bind}</b>" if n.bind else n.role
            lines.append(f'  {n.name}["{label}"]')
        elif n.kind == ControlKind.DECISION:
            lines.append(f"  {n.name}{{{n.name}}}")
        else:
            lines.append(f"  {n.name}(((end)))")
    for e in comp.data:
        a = "in" if e.source.node == "self" else e.source.node
        if e.target.node == "self":
            continue
        p = lib.effective_params(comp.node(e.target.node).effective).get(e.target.param) \
            if comp.node(e.target.node) else None
        lab = p.type if p else e.target.param
        lines.append(f"  {a} -->|{lab}| {e.target.node}")
    for c in comp.control:
        if c.kind == ControlEdgeKind.INVOKES:
            lines.append(f"  {c.source} -.->|invokes| {c.target}")
        elif c.kind == ControlEdgeKind.REPAIR:
            lines.append(f"  {c.source} -.->|repair ≤{c.bound}| {c.target}")
        else:
            lab = f"|{c.guard}|" if c.guard else ""
            lines.append(f"  {c.source} -->{lab} {c.target}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- output

def generate(lib: Library, out_dir: str, provenance: bool = True) -> list[str]:
    """Write one skill folder per concrete skill. Returns generated names."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name, sk in sorted(lib.skills.items()):
        if sk.abstract:
            continue
        if isinstance(sk, CompositeSkill):
            if not is_executable(lib, sk):
                continue
            text = render_workflow(lib, sk, provenance)
        else:
            text = render_skill(lib, name, provenance)
        d = os.path.join(out_dir, name)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        for s in lib.skill_ancestors(name):
            for res in lib.skills[s].resources:
                dst = os.path.join(d, res.path)
                if os.path.exists(dst):
                    continue  # nearest declaration wins
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(os.path.join(lib.root, res.source), dst)
        for fname, src in upstream_licenses(lib, name).items():
            shutil.copyfile(os.path.join(lib.root, src), os.path.join(d, fname))
        if isinstance(sk, CompositeSkill):
            os.makedirs(os.path.join(d, "references"), exist_ok=True)
            with open(os.path.join(d, "references", "workflow.mmd"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(mermaid(lib, sk))
        written.append(name)
    return written
