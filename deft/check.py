"""Constraint checking for DEFT libraries.

WF   well-formedness: every reference resolves (types, parents, nodes, ports);
     a skill specializes a skill of its own kind (atomic or composite);
     bundled resources live in the folder of their kind; imported origins and
     sections read from upstream files go together
T1   both hierarchies are acyclic and single-parent
T2   a concrete skill implements every abstract section it inherits
T3   a refinement targets a section inherited from an ancestor, with the
     right effective kind (implements->abstract, overrides/extends->default);
     final sections, declared or sealed, admit no refinement and inherited
     sections are not redeclared
T4   a parameter redeclared by a descendant keeps its direction and narrows
     the inherited type; a property redeclared by a subtype narrows the
     inherited multiplicity
C1   every binding is concrete and specializes its role
C2   every data edge (and repair payload) is type-safe on the effective
     skills, with compatible multiplicities
C3   every mandatory input of a skill node, and every mandatory output of
     the composite, receives a data edge
C4   without repair edges the graph is acyclic; every repair edge has an
     iteration bound; an invoked node is reached only through its caller
C5   for every node n, the postconditions of its predecessors and the guards
     that reach n jointly entail pre(n): natural language, so it is not
     decided here; see obligations()
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import (MANY, RESOURCE_FOLDER, AtomicSkill, CompositeSkill, ControlEdgeKind,
                    ControlNode, DataEdge, Direction, Library, OriginMode,
                    Parameter, RefinementKind, SectionKind, SkillNode)
from .resolve import resolve


@dataclass(frozen=True)
class Violation:
    code: str
    element: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.element}: {self.message}"


# ---------------------------------------------------------------- helpers

def _has_cycle(name: str, table: dict) -> bool:
    seen, cur = set(), name
    while cur is not None and cur in table:
        if cur in seen:
            return True
        seen.add(cur)
        cur = table[cur].parent
    return False


def _fmt_mult(p: Parameter) -> str:
    up = "*" if p.upper == MANY else str(p.upper)
    return f"[{p.lower}..{up}]"


# ---------------------------------------------------------------- WF + S

def check_well_formed(lib: Library) -> list[Violation]:
    v = []
    for t in lib.types.values():
        if t.parent and t.parent not in lib.types:
            v.append(Violation("WF", f"type {t.name}", f"unknown parent type '{t.parent}'"))
    for s in lib.skills.values():
        if s.parent and s.parent not in lib.skills:
            v.append(Violation("WF", f"skill {s.name}", f"unknown parent skill '{s.parent}'"))
        elif s.parent and isinstance(s, CompositeSkill) != isinstance(lib.skills[s.parent], CompositeSkill):
            v.append(Violation("WF", f"skill {s.name}",
                               f"specializes '{s.parent}', which is not of its kind (atomic or composite)"))
        for p in s.parameters:
            if p.type not in lib.types:
                v.append(Violation("WF", f"skill {s.name}", f"parameter '{p.name}' has unknown type '{p.type}'"))
        for r in s.resources:
            folder = RESOURCE_FOLDER[r.kind]
            if r.path.replace("\\", "/").split("/")[0] != folder:
                v.append(Violation("WF", f"skill {s.name}",
                                   f"{r.kind.value} resource '{r.path}' must live under {folder}/"))
        sourced = [x.source for x in list(getattr(s, "sections", [])) + list(getattr(s, "refinements", []))
                   if x.source]
        imported = any(o.mode == OriginMode.IMPORTED for o in s.origin)
        if sourced and not imported:
            v.append(Violation("WF", f"skill {s.name}",
                               f"content is read from '{sourced[0]}' but no imported origin is declared"))
        if imported and not sourced:
            v.append(Violation("WF", f"skill {s.name}",
                               "declares an imported origin but no section reads upstream content"))
    return v


def check_t1(lib: Library) -> list[Violation]:
    v = []
    for t in lib.types:
        if _has_cycle(t, lib.types):
            v.append(Violation("T1", f"type {t}", "type hierarchy is cyclic"))
    for s in lib.skills:
        if _has_cycle(s, lib.skills):
            v.append(Violation("T1", f"skill {s}", "skill hierarchy is cyclic"))
    return v


def _acyclic(lib: Library, name: str) -> bool:
    return not _has_cycle(name, lib.skills)


def check_t2(lib: Library) -> list[Violation]:
    v = []
    for s in lib.skills.values():
        if s.abstract or not _acyclic(lib, s.name):
            continue
        r = resolve(lib, s.name)
        for sec in r.sections:
            if not sec.filled:
                v.append(Violation("T2", f"skill {s.name}",
                                   f"concrete skill leaves abstract section '{sec.name}' "
                                   f"(declared by {sec.sources[0].skill}) unimplemented"))
    return v


def check_t3(lib: Library) -> list[Violation]:
    v = []
    for s in lib.skills.values():
        if not isinstance(s, AtomicSkill) or not _acyclic(lib, s.name):
            continue
        inherited = {}
        if s.parent in lib.skills and isinstance(lib.skills[s.parent], AtomicSkill):
            inherited = {sec.name: sec for sec in resolve(lib, s.parent).sections}
        for sec in s.sections:
            if sec.name in inherited:
                v.append(Violation("T3", f"skill {s.name}",
                                   f"redeclares section '{sec.name}' inherited from {inherited[sec.name].sources[0].skill}"))
        for ref in s.refinements:
            sec = inherited.get(ref.target)
            if sec is None:
                v.append(Violation("T3", f"skill {s.name}",
                                   f"{ref.kind.value} targets '{ref.target}', which no ancestor declares"))
                continue
            if sec.kind == SectionKind.FINAL:
                by = f"sealed by {sec.sealed_by}" if sec.sealed_by else f"declared by {sec.sources[0].skill}"
                v.append(Violation("T3", f"skill {s.name}",
                                   f"{ref.kind.value} targets final section '{ref.target}' ({by})"))
            elif ref.kind == RefinementKind.IMPLEMENTS and sec.kind != SectionKind.ABSTRACT:
                v.append(Violation("T3", f"skill {s.name}",
                                   f"implements targets {sec.kind.value} section '{ref.target}' (expected abstract)"))
            elif ref.kind in (RefinementKind.OVERRIDES, RefinementKind.EXTENDS) and sec.kind != SectionKind.DEFAULT:
                v.append(Violation("T3", f"skill {s.name}",
                                   f"{ref.kind.value} targets {sec.kind.value} section '{ref.target}' (expected default)"))
    return v


def check_t4(lib: Library) -> list[Violation]:
    v = []
    for s in lib.skills.values():
        if not s.parent or not _acyclic(lib, s.name):
            continue
        for p in s.parameters:
            inherited = lib.effective_param(s.parent, p.name)
            if inherited is None:
                continue
            if p.direction != inherited.direction:
                v.append(Violation("T4", f"skill {s.name}",
                                   f"parameter '{p.name}' changes direction ({inherited.direction.value} -> {p.direction.value})"))
            elif p.type in lib.types and inherited.type in lib.types and not lib.conforms_type(p.type, inherited.type):
                v.append(Violation("T4", f"skill {s.name}",
                                   f"parameter '{p.name}': {p.type} does not specialize inherited {inherited.type}"))
    for t in lib.types.values():
        if not t.parent or _has_cycle(t.name, lib.types):
            continue
        for p in t.properties:
            inherited = lib.effective_property(t.parent, p.name)
            if inherited is None:
                continue
            if not _within(p.lower, p.upper, inherited.lower, inherited.upper):
                v.append(Violation("T4", f"type {t.name}",
                                   f"property '{p.name}' {_fmt_mult(p)} widens inherited {_fmt_mult(inherited)}"))
    return v


def _within(lower: int, upper: int, inh_lower: int, inh_upper: int) -> bool:
    """[lower..upper] is contained in [inh_lower..inh_upper] (MANY = unbounded)."""
    if lower < inh_lower:
        return False
    if inh_upper == MANY:
        return True
    return upper != MANY and upper <= inh_upper


# ---------------------------------------------------------------- C

def _port_param(lib: Library, comp: CompositeSkill, node_id: str, pname: str):
    """Return (parameter, effective skill name) of a port, or (None, reason)."""
    if node_id == "self":
        p = lib.effective_params(comp.name).get(pname)
        return (p, comp.name) if p else (None, f"composite has no parameter '{pname}'")
    node = comp.node(node_id)
    if node is None:
        return None, f"unknown node '{node_id}'"
    if not isinstance(node, SkillNode):
        return None, f"node '{node_id}' is a control node"
    if node.effective not in lib.skills:
        return None, f"node '{node_id}' refers to unknown skill '{node.effective}'"
    p = lib.effective_params(node.effective).get(pname)
    return (p, node.effective) if p else (None, f"{node.effective} has no parameter '{pname}'")


def _check_edge_types(lib: Library, comp: CompositeSkill, e: DataEdge, label: str) -> list[Violation]:
    v = []
    src, s_owner = _port_param(lib, comp, e.source.node, e.source.param)
    tgt, t_owner = _port_param(lib, comp, e.target.node, e.target.param)
    where = f"workflow {comp.name}"
    if src is None:
        return [Violation("WF", where, f"{label} {e.source} -> {e.target}: {s_owner}")]
    if tgt is None:
        return [Violation("WF", where, f"{label} {e.source} -> {e.target}: {t_owner}")]
    # Direction: an edge leaves an output of a node (or an input of the
    # composite) and enters an input of a node (or an output of the composite).
    # An inout parameter is both an input and an output.
    src_ok = src.direction.is_input if e.source.node == "self" else src.direction.is_output
    tgt_ok = tgt.direction.is_output if e.target.node == "self" else tgt.direction.is_input
    if not (src_ok and tgt_ok):
        v.append(Violation("WF", where, f"{label} {e.source} -> {e.target}: wrong parameter direction"))
        return v
    if src.type in lib.types and tgt.type in lib.types and not lib.conforms_type(src.type, tgt.type):
        v.append(Violation("C2", where,
                           f"{label} {e.source} -> {e.target}: {src.type} (from {s_owner}) "
                           f"does not conform to {tgt.type} (required by {t_owner})"))
    if tgt.upper != MANY and (src.upper == MANY or src.upper > tgt.upper):
        v.append(Violation("C2", where,
                           f"{label} {e.source} -> {e.target}: multiplicity {_fmt_mult(src)} "
                           f"exceeds {_fmt_mult(tgt)}"))
    return v


def check_c1(lib: Library, comp: CompositeSkill) -> list[Violation]:
    v, where = [], f"workflow {comp.name}"
    for n in comp.skill_nodes():
        if n.role not in lib.skills:
            v.append(Violation("WF", where, f"node '{n.name}' has unknown role '{n.role}'"))
            continue
        if n.bind is None:
            continue
        if n.bind not in lib.skills:
            v.append(Violation("WF", where, f"node '{n.name}' is bound to unknown skill '{n.bind}'"))
            continue
        if lib.skills[n.bind].abstract:
            v.append(Violation("C1", where, f"node '{n.name}' is bound to abstract skill '{n.bind}'"))
        if not lib.conforms_skill(n.bind, n.role):
            v.append(Violation("C1", where, f"node '{n.name}': {n.bind} does not specialize role {n.role}"))
    return v


def check_c2(lib: Library, comp: CompositeSkill) -> list[Violation]:
    v = []
    for e in comp.data:
        v += _check_edge_types(lib, comp, e, "data edge")
    for c in comp.control:
        if c.carries is not None:
            v += _check_edge_types(lib, comp, c.carries, "repair payload")
    return v


def check_c3(lib: Library, comp: CompositeSkill) -> list[Violation]:
    v, where = [], f"workflow {comp.name}"
    fed = {(e.target.node, e.target.param) for e in comp.data}
    callers = {c.target: c.source for c in comp.control if c.kind == ControlEdgeKind.INVOKES}
    for n in comp.skill_nodes():
        if n.effective not in lib.skills:
            continue
        for p in lib.effective_params(n.effective).values():
            if not p.direction.is_input or not p.mandatory or (n.name, p.name) in fed:
                continue
            caller = comp.node(callers.get(n.name, ""))
            if isinstance(caller, SkillNode) and caller.effective in lib.skills and any(
                    q.type in lib.types and p.type in lib.types and lib.conforms_type(q.type, p.type)
                    for q in lib.effective_params(caller.effective).values()):
                continue  # supplied by the invoking skill's context
            v.append(Violation("C3", where, f"mandatory input {n.name}.{p.name} ({p.type}) receives no data edge"))
    for p in lib.effective_params(comp.name).values():
        if p.direction.is_output and p.mandatory and ("self", p.name) not in fed:
            v.append(Violation("C3", where, f"mandatory output self.{p.name} ({p.type}) receives no data edge"))
    return v


def check_c4(lib: Library, comp: CompositeSkill) -> list[Violation]:
    v, where = [], f"workflow {comp.name}"
    ids = {n.name for n in comp.nodes}
    for c in comp.control:
        for end in (c.source, c.target):
            if end not in ids:
                v.append(Violation("WF", where, f"{c.kind.value} edge refers to unknown node '{end}'"))
    # acyclicity of everything but repair edges
    succ: dict[str, set[str]] = {n: set() for n in ids}
    for e in comp.data:
        if e.source.node in succ and e.target.node in ids:
            succ[e.source.node].add(e.target.node)
    for c in comp.control:
        if c.kind != ControlEdgeKind.REPAIR and c.source in succ and c.target in ids:
            succ[c.source].add(c.target)
    color = {n: 0 for n in succ}

    def dfs(n) -> bool:
        color[n] = 1
        for m in succ[n]:
            if color[m] == 1 or (color[m] == 0 and dfs(m)):
                return True
        color[n] = 2
        return False
    if any(color[n] == 0 and dfs(n) for n in sorted(succ)):
        v.append(Violation("C4", where, "the graph without repair edges is cyclic"))
    for c in comp.control:
        if c.kind == ControlEdgeKind.REPAIR and (not isinstance(c.bound, int) or c.bound < 1):
            v.append(Violation("C4", where, f"repair edge {c.source} -> {c.target} has no iteration bound"))
    invoked: dict[str, list[str]] = {}
    for c in comp.control:
        if c.kind == ControlEdgeKind.INVOKES:
            invoked.setdefault(c.target, []).append(c.source)
    for target, sources in invoked.items():
        if len(sources) > 1:
            v.append(Violation("C4", where, f"node '{target}' is invoked by several nodes: {sorted(sources)}"))
        others = [c for c in comp.control if c.target == target and c.kind != ControlEdgeKind.INVOKES]
        if others:
            v.append(Violation("C4", where, f"invoked node '{target}' is also reached by a "
                                            f"{others[0].kind.value} edge from '{others[0].source}'"))
    for n in comp.nodes:
        if isinstance(n, ControlNode) and n.kind.value == "decision":
            outs = [c for c in comp.control if c.source == n.name]
            if any(c.guard is None for c in outs) or len(outs) < 2:
                v.append(Violation("WF", where, f"decision '{n.name}' needs two or more guarded outgoing edges"))
    return v


def check_composite(lib: Library, comp: CompositeSkill) -> list[Violation]:
    return check_c1(lib, comp) + check_c2(lib, comp) + check_c3(lib, comp) + check_c4(lib, comp)


def check_library(lib: Library) -> list[Violation]:
    v = check_well_formed(lib) + check_t1(lib) + check_t2(lib) + check_t3(lib) + check_t4(lib)
    for s in lib.skills.values():
        if isinstance(s, CompositeSkill):
            v += check_composite(lib, s)
    # deterministic order, no duplicates
    return sorted(set(v), key=lambda x: (x.code, x.element, x.message))


def is_executable(lib: Library, comp: CompositeSkill) -> bool:
    """Every node is performed by a concrete skill."""
    return all(n.effective in lib.skills and not lib.skills[n.effective].abstract
               for n in comp.skill_nodes())


# ---------------------------------------------------------------- C5

@dataclass
class Obligation:
    target: str           # node id, or "self" for the composite's postconditions
    sources: list[str]    # predecessors whose guarantees are assumed
    post: list[str]       # guarantees: postconditions of the predecessors and guards
    pre: list[str]        # what must follow: preconditions of the target

    @property
    def edge(self) -> str:
        return f"{', '.join(self.sources)} -> {self.target}"


def obligations(lib: Library, comp: CompositeSkill) -> list[Obligation]:
    """C5 proof obligations, one per node n: the postconditions of all the
    predecessors of n (and the guards of the edges that reach n) jointly
    entail pre(n), under the composite's preconditions taken as assumptions.
    For the composite itself, the guarantees of the nodes that
    feed its outputs, plus the guard that reaches the final node, entail its
    postconditions. Decision nodes pass on the guarantees of their own
    predecessors."""
    preds: dict[str, list[tuple[str, str | None]]] = {}
    for e in comp.data:
        preds.setdefault(e.target.node, []).append((e.source.node, None))
    for c in comp.control:
        preds.setdefault(c.target, []).append((c.source, c.guard))

    def guarantees(node_id: str, seen: frozenset = frozenset()) -> list[str]:
        if node_id == "self":
            return list(comp.pre)
        node = comp.node(node_id)
        if isinstance(node, SkillNode):
            return list(lib.effective_conditions(node.effective)[1]) if node.effective in lib.skills else []
        out = []  # control node: forward what reaches it
        for src, guard in preds.get(node_id, []):
            if src not in seen:
                out += guarantees(src, seen | {node_id})
        return out

    def collect(target: str) -> tuple[list[str], list[str]]:
        # the composite's preconditions are assumptions that hold for every step
        sources, post = [], list(comp.pre)
        for src, guard in preds.get(target, []):
            if src not in sources:
                sources.append(src)
            for c in guarantees(src) + ([guard] if guard else []):
                if c not in post:
                    post.append(c)
        return sources, post

    out = []
    for n in comp.skill_nodes():
        pre = lib.effective_conditions(n.effective)[0] if n.effective in lib.skills else []
        if pre:
            sources, post = collect(n.name)
            out.append(Obligation(n.name, sources, post, list(pre)))
    if comp.post:
        sources, post = collect("self")
        for f in comp.nodes:
            if isinstance(f, ControlNode) and f.kind.value == "final":
                fs, fp = collect(f.name)
                sources += [x for x in fs if x not in sources]
                post += [x for x in fp if x not in post]
        out.append(Obligation("self", sources, post, list(comp.post)))
    return out
