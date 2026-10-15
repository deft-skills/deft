"""PlantUML export of DEFT libraries and workflows."""
from __future__ import annotations

from .generate import _mult
from .model import (CompositeSkill, ControlEdgeKind, ControlKind, ControlNode,
                    Library, SkillNode)

_STYLE = """!theme plain
hide circle
hide empty members
skinparam classAttributeIconSize 0
skinparam shadowing false
skinparam defaultFontName Helvetica
skinparam defaultFontSize 13
skinparam ArrowFontSize 11
skinparam class {
  BackgroundColor white
  BorderColor #333333
  HeaderBackgroundColor #EEEEEE
}
skinparam package {
  BorderColor #999999
  FontStyle plain
}
"""


def _q(name: str) -> str:
    return '"' + name + '"'


def plantuml_library(lib: Library) -> str:
    """Skill families and the artifact-type hierarchy.

    Each skill shows only what it declares or narrows: its own parameters and
    the sections it declares (abstract ones in italics) or refines.
    """
    out = ["@startuml", _STYLE, "top to bottom direction"]
    families: dict[str, list] = {}
    for s in lib.skills.values():
        if not isinstance(s, CompositeSkill):
            families.setdefault(s.family, []).append(s)
    for fam, skills in sorted(families.items()):
        out.append(f'package "{fam}" {{')
        for s in skills:
            kw = "abstract class" if s.abstract else "class"
            out.append(f"  {kw} {_q(s.name)} {{")
            for p in s.parameters:
                arrow = p.direction.value
                out.append(f"    {arrow} {p.name} : {p.type} [{_mult(p)}]")
            marks = [f"{sec.kind.value[0].upper()}:{sec.name}" for sec in getattr(s, "sections", [])]
            marks += [f"{r.kind.value[0]}:{r.target}" for r in getattr(s, "refinements", [])]
            if marks:
                out.append("    --")
                out.append("    " + "  ".join(marks))
            out.append("  }")
        out.append("}")
    out.append('package "artifact types" {')
    for t in lib.types.values():
        kw = "abstract class" if t.abstract else "class"
        props = [f"{p.name} [{p.lower}..{'*' if p.upper < 0 else p.upper}]" for p in t.properties
                 if (p.lower, p.upper) != (1, 1)]
        body = "".join(f"\n    {x}" for x in props)
        out.append(f"  {kw} {t.name} {{{body}\n  }}")
    out.append("}")
    for s in lib.skills.values():
        if s.parent and not isinstance(s, CompositeSkill):
            out.append(f"{_q(s.parent)} <|-- {_q(s.name)}")
    for t in lib.types.values():
        if t.parent:
            out.append(f"{t.parent} <|-- {t.name}")
    out.append("@enduml")
    return "\n".join(out) + "\n"


def plantuml_workflow(lib: Library, comp: CompositeSkill) -> str:
    out = ["@startuml", _STYLE, "left to right direction",
           "skinparam rectangle {\n  BackgroundColor white\n  BorderColor #333333\n  RoundCorner 12\n}",
           'circle " " as wf_in']
    for n in comp.nodes:
        nid = n.name.replace("-", "_")
        if isinstance(n, SkillNode):
            label = f"<i>{n.role}</i>\\n<b>{n.bind}</b>" if n.bind else n.role
            out.append(f'rectangle "{label}" as {nid}')
        elif isinstance(n, ControlNode) and n.kind == ControlKind.DECISION:
            out.append(f'hexagon "{n.name}" as {nid}')
        else:
            out.append(f'circle "end" as {nid}')

    def ref(x):
        return "wf_in" if x == "self" else x.replace("-", "_")
    for e in comp.data:
        if e.target.node == "self":
            continue
        node = comp.node(e.target.node)
        p = lib.effective_params(node.effective).get(e.target.param) if isinstance(node, SkillNode) else None
        out.append(f"{ref(e.source.node)} --> {ref(e.target.node)} : {p.type if p else e.target.param}")
    for c in comp.control:
        if c.kind == ControlEdgeKind.INVOKES:
            out.append(f"{ref(c.source)} ..> {ref(c.target)} : invokes")
        elif c.kind == ControlEdgeKind.REPAIR:
            out.append(f"{ref(c.source)} ..> {ref(c.target)} : repair ≤{c.bound}")
        else:
            g = f" : [{c.guard}]" if c.guard else ""
            out.append(f"{ref(c.source)} ..> {ref(c.target)}{g}")
    out.append("@enduml")
    return "\n".join(out) + "\n"
