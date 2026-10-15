"""E2 (checkability): mutation analysis of the constraint checker.

Each mutation operator seeds one fault that violates one constraint by
construction, at every applicable location of the running-example library.
A mutant is *killed* when the checker reports a violation, and *killed as
intended* when the violation has the targeted constraint code. The
unmutated library must yield no violation (no false positives).

Output: results/e2_mutation.json
"""
from __future__ import annotations

import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import MODELS, save  # noqa: E402

from deft.check import check_library  # noqa: E402
from deft.loader import load_library  # noqa: E402
from deft.resolve import resolve  # noqa: E402
from dataclasses import replace  # noqa: E402

from deft.model import (MANY, CompositeSkill, ControlEdge,  # noqa: E402
                        ControlEdgeKind, Direction, OriginMode, Port,
                        Refinement, RefinementKind, ResourceKind, Section,
                        SectionKind, SkillNode)


def _skills(lib):
    return [s for s in lib.skills.values() if not isinstance(s, CompositeSkill)]


def _workflows(lib):
    return [s for s in lib.skills.values() if isinstance(s, CompositeSkill)]


# ------------------------------------------------------------- operators
# Each operator yields (location, mutate) where mutate(lib) edits a copy.

def t1_skill_cycle(lib):
    """Make a root skill the child of one of its descendants."""
    for s in _skills(lib):
        if s.parent is None:
            for d in _skills(lib):
                if d.name != s.name and s.name in lib.skill_ancestors(d.name):
                    yield f"{s.name}.parent={d.name}", lambda L, s=s.name, d=d.name: setattr(L.skills[s], "parent", d)


def t1_type_cycle(lib):
    for t in lib.types.values():
        if t.parent is None:
            for d in lib.types.values():
                if d.name != t.name and t.name in lib.type_ancestors(d.name):
                    yield f"{t.name}.parent={d.name}", lambda L, t=t.name, d=d.name: setattr(L.types[t], "parent", d)


def t2_drop_implementation(lib):
    for s in _skills(lib):
        if s.abstract:
            continue
        for i, r in enumerate(s.refinements):
            if r.kind == RefinementKind.IMPLEMENTS:
                yield f"{s.name}-implements:{r.target}", lambda L, s=s.name, i=i: L.skills[s].refinements.pop(i)


def _inherited(lib, name):
    """Effective kind of every section a skill inherits from its parent."""
    parent = lib.skills[name].parent
    if parent is None:
        return {}
    return {sec.name: sec.kind for sec in resolve(lib, parent).sections}


def t3_refine_final(lib):
    """Override an inherited final section."""
    for s in _skills(lib):
        for sec, kind in _inherited(lib, s.name).items():
            if kind == SectionKind.FINAL:
                yield f"{s.name} overrides {sec}", lambda L, s=s.name, sec=sec: L.skills[s].refinements.append(
                    Refinement(RefinementKind.OVERRIDES, sec, "changed"))


def t3_wrong_kind(lib):
    """Swap implements <-> overrides on an existing refinement."""
    for s in _skills(lib):
        for i, r in enumerate(s.refinements):
            new = RefinementKind.OVERRIDES if r.kind == RefinementKind.IMPLEMENTS else RefinementKind.IMPLEMENTS
            yield f"{s.name}:{r.target} {r.kind.value}->{new.value}", \
                lambda L, s=s.name, i=i, new=new: setattr(L.skills[s].refinements[i], "kind", new)


def t3_redeclare(lib):
    """Redeclare an inherited section instead of refining it."""
    for s in _skills(lib):
        for sec in _inherited(lib, s.name):
            yield f"{s.name} redeclares {sec}", lambda L, s=s.name, sec=sec: L.skills[s].sections.append(
                Section(sec, SectionKind.FINAL, "", "copy"))


def _seal_and_refine(L, s, i, child):
    ref = L.skills[s].refinements[i]
    ref.final = True
    L.skills[child].refinements.append(Refinement(RefinementKind.OVERRIDES, ref.target, "changed"))


def t3_refine_sealed(lib):
    """Seal a refinement, then refine the same section again in a child."""
    for s in _skills(lib):
        for i, r in enumerate(s.refinements):
            for c in _skills(lib):
                if c.parent == s.name:
                    yield f"{s.name} seals {r.target}, {c.name} overrides it", \
                        lambda L, s=s.name, i=i, c=c.name: _seal_and_refine(L, s, i, c)


def t4_widen(lib):
    """Redeclare a parameter with a type that does not specialize the inherited one."""
    for s in _skills(lib):
        if not s.parent:
            continue
        for i, p in enumerate(s.parameters):
            inh = lib.effective_param(s.parent, p.name)
            if inh is None:
                continue
            for t in sorted(lib.types):
                if not lib.conforms_type(t, inh.type):
                    yield f"{s.name}.{p.name}:{p.type}->{t}", \
                        lambda L, s=s.name, i=i, t=t: setattr(L.skills[s].parameters[i], "type", t)
                    break


def t4_direction(lib):
    for s in _skills(lib):
        if not s.parent:
            continue
        for i, p in enumerate(s.parameters):
            if lib.effective_param(s.parent, p.name) is not None:
                new = Direction.OUT if p.direction == Direction.IN else Direction.IN
                yield f"{s.name}.{p.name} direction", \
                    lambda L, s=s.name, i=i, new=new: setattr(L.skills[s].parameters[i], "direction", new)


def t4_widen_property(lib):
    """Redeclare an inherited property in a subtype with a looser multiplicity."""
    for t in lib.types.values():
        if not t.parent:
            continue
        own = {p.name for p in t.properties}
        for p in lib.effective_properties(t.parent):
            if p.name in own:
                continue
            if p.lower > 0:
                lower, upper = p.lower - 1, p.upper
            elif p.upper != MANY:
                lower, upper = p.lower, MANY
            else:
                continue
            yield f"{t.name}.{p.name} [{lower}..{'*' if upper == MANY else upper}]", \
                lambda L, t=t.name, p=p, lo=lower, up=upper: L.types[t].properties.append(
                    replace(p, lower=lo, upper=up))


def wf_cross_kind_parent(lib):
    """Make a workflow specialize an atomic skill, or a root atomic skill a workflow."""
    roots = [s for s in _skills(lib) if s.parent is None]
    for w in _workflows(lib):
        if w.parent is None:
            for a in roots:
                yield f"{w.name}.parent={a.name}", lambda L, w=w.name, a=a.name: setattr(L.skills[w], "parent", a)
        for a in roots:
            yield f"{a.name}.parent={w.name}", lambda L, w=w.name, a=a.name: setattr(L.skills[a], "parent", w)


def wf_resource_kind(lib):
    """Declare a bundled resource with a kind that does not match its folder."""
    for s in _skills(lib):
        for i, r in enumerate(s.resources):
            for k in ResourceKind:
                if k != r.kind:
                    yield f"{s.name}:{r.path} as {k.value}", \
                        lambda L, s=s.name, i=i, k=k: setattr(L.skills[s].resources[i], "kind", k)


def wf_origin_mode(lib):
    """Flip an origin between adapted and imported."""
    for s in _skills(lib):
        for i, o in enumerate(s.origin):
            new = OriginMode.ADAPTED if o.mode == OriginMode.IMPORTED else OriginMode.IMPORTED
            if new == OriginMode.IMPORTED and any(x.mode == OriginMode.IMPORTED for x in s.origin):
                continue
            if new == OriginMode.ADAPTED and sum(x.mode == OriginMode.IMPORTED for x in s.origin) > 1:
                continue
            yield f"{s.name}:{o.repo} {o.mode.value}->{new.value}", \
                lambda L, s=s.name, i=i, new=new: setattr(L.skills[s].origin[i], "mode", new)


def c1_bind_abstract(lib):
    for w in _workflows(lib):
        for n in w.skill_nodes():
            for a in sorted(lib.skills):
                if lib.skills[a].abstract and lib.conforms_skill(a, n.role) and a != n.bind:
                    yield f"{w.name}.{n.name}->{a}", lambda L, w=w.name, n=n.name, a=a: setattr(L.skills[w].node(n), "bind", a)


def c1_bind_unrelated(lib):
    for w in _workflows(lib):
        for n in w.skill_nodes():
            for a in sorted(lib.skills):
                sk = lib.skills[a]
                if not sk.abstract and not isinstance(sk, CompositeSkill) and not lib.conforms_skill(a, n.role):
                    yield f"{w.name}.{n.name}->{a}", lambda L, w=w.name, n=n.name, a=a: setattr(L.skills[w].node(n), "bind", a)
                    break


def c2_redirect(lib):
    """Redirect a data edge to a source output whose type does not conform."""
    for w in _workflows(lib):
        for i, e in enumerate(w.data):
            if e.target.node == "self":
                continue
            tgt = lib.effective_params(w.node(e.target.node).effective)[e.target.param]
            for n in w.skill_nodes():
                if n.name in (e.target.node, e.source.node):
                    continue
                for p in lib.effective_params(n.effective).values():
                    if p.direction == Direction.OUT and not lib.conforms_type(p.type, tgt.type):
                        yield f"{w.name}: {n.name}.{p.name} -> {e.target}", \
                            lambda L, w=w.name, i=i, n=n.name, p=p.name: setattr(L.skills[w].data[i], "source", Port(n, p))
                        break
                else:
                    continue
                break


def c3_drop_edge(lib):
    """Remove the only data edge feeding a mandatory input."""
    for w in _workflows(lib):
        for i, e in enumerate(w.data):
            same = [x for x in w.data if (x.target.node, x.target.param) == (e.target.node, e.target.param)]
            if len(same) != 1:
                continue
            if e.target.node == "self":
                p = lib.effective_params(w.name)[e.target.param]
            else:
                p = lib.effective_params(w.node(e.target.node).effective)[e.target.param]
            if p.mandatory:
                yield f"{w.name}: drop {e.source} -> {e.target}", lambda L, w=w.name, i=i: L.skills[w].data.pop(i)


def c4_unbound_repair(lib):
    for w in _workflows(lib):
        for i, c in enumerate(w.control):
            if c.kind == ControlEdgeKind.REPAIR:
                yield f"{w.name}: {c.source}->{c.target} unbounded", \
                    lambda L, w=w.name, i=i: setattr(L.skills[w].control[i], "bound", None)


def c4_repair_as_sequence(lib):
    for w in _workflows(lib):
        for i, c in enumerate(w.control):
            if c.kind == ControlEdgeKind.REPAIR:
                yield f"{w.name}: {c.source}->{c.target} as sequence", \
                    lambda L, w=w.name, i=i: setattr(L.skills[w].control[i], "kind", ControlEdgeKind.SEQUENCE)


def c4_back_edge(lib):
    """Add a sequence edge from a node back to one of its data predecessors."""
    for w in _workflows(lib):
        for e in w.data:
            if "self" in (e.source.node, e.target.node):
                continue
            yield f"{w.name}: {e.target.node}->{e.source.node}", lambda L, w=w.name, a=e.target.node, b=e.source.node: \
                L.skills[w].control.append(ControlEdge(ControlEdgeKind.SEQUENCE, a, b))


def c4_reach_invoked(lib):
    for w in _workflows(lib):
        for c in w.control:
            if c.kind == ControlEdgeKind.INVOKES:
                for n in w.skill_nodes():
                    if n.name not in (c.source, c.target):
                        yield f"{w.name}: {n.name}->{c.target}", lambda L, w=w.name, a=n.name, b=c.target: \
                            L.skills[w].control.append(ControlEdge(ControlEdgeKind.SEQUENCE, a, b))
                        break


OPERATORS = [
    ("T1", "skill-cycle", t1_skill_cycle),
    ("T1", "type-cycle", t1_type_cycle),
    ("T2", "drop-implementation", t2_drop_implementation),
    ("T3", "refine-final-section", t3_refine_final),
    ("T3", "refine-sealed-section", t3_refine_sealed),
    ("T3", "swap-refinement-kind", t3_wrong_kind),
    ("T3", "redeclare-inherited-section", t3_redeclare),
    ("T4", "widen-parameter-type", t4_widen),
    ("T4", "flip-parameter-direction", t4_direction),
    ("T4", "widen-property-multiplicity", t4_widen_property),
    ("WF", "cross-kind-parent", wf_cross_kind_parent),
    ("WF", "mismatch-resource-kind", wf_resource_kind),
    ("WF", "flip-origin-mode", wf_origin_mode),
    ("C1", "bind-abstract-skill", c1_bind_abstract),
    ("C1", "bind-unrelated-skill", c1_bind_unrelated),
    ("C2", "redirect-ill-typed-edge", c2_redirect),
    ("C3", "drop-mandatory-input-edge", c3_drop_edge),
    ("C4", "unbound-repair-edge", c4_unbound_repair),
    ("C4", "repair-as-sequence", c4_repair_as_sequence),
    ("C4", "back-edge", c4_back_edge),
    ("C4", "reach-invoked-node", c4_reach_invoked),
]


def main() -> dict:
    base = load_library(MODELS)
    baseline = [str(v) for v in check_library(base)]
    rows, mutants = [], []
    for code, op, fn in OPERATORS:
        n = killed = intended = exclusive = 0
        for loc, mutate in fn(base):
            lib = copy.deepcopy(base)
            mutate(lib)
            found = check_library(lib)
            codes = sorted({v.code for v in found})
            n += 1
            killed += bool(found)
            intended += code in codes
            exclusive += codes == [code]
            mutants.append({"constraint": code, "operator": op, "location": loc, "reported": codes})
        rows.append({"constraint": code, "operator": op, "mutants": n, "killed": killed, "intended": intended,
                     "exclusive": exclusive})
    by_constraint = {}
    for r in rows:
        agg = by_constraint.setdefault(r["constraint"], {"mutants": 0, "killed": 0, "intended": 0, "exclusive": 0})
        for k in ("mutants", "killed", "intended", "exclusive"):
            agg[k] += r[k]
    total = {k: sum(r[k] for r in rows) for k in ("mutants", "killed", "intended", "exclusive")}
    result = {"baseline_violations": baseline, "operators": rows, "by_constraint": by_constraint,
              "total": total, "mutants": mutants}
    save("e2_mutation.json", result)
    return result


if __name__ == "__main__":
    r = main()
    print("baseline violations:", len(r["baseline_violations"]))
    for row in r["operators"]:
        print(f"{row['constraint']:3} {row['operator']:30} {row['killed']:4}/{row['mutants']:<4} intended {row['intended']} exclusive {row['exclusive']}")
    print("by constraint:", r["by_constraint"])
    print("total:", r["total"])
