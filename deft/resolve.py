"""Resolution of a skill into the instruction set an agent receives.

resolve(s):
  1. collect the ancestors of s, from the root down to s;
  2. take the sections of the root;
  3. for each descendant in that order, apply its refinements (and append
     the new sections it declares), recording it as the source of every
     section it changes.

A section keeps the kind it was declared with until it is refined: an
implemented, overridden or extended section becomes default, so further
descendants may refine it again, or final if the refinement seals it.

Section content may contain placeholders ``{{name}}`` or ``{{meta.<key>}}``,
substituted with the attributes of the skill being resolved, so that a
fixed section can be shared verbatim by a whole family.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .model import Library, RefinementKind, SectionKind


@dataclass
class Contribution:
    skill: str
    action: str  # declares | implements | overrides | extends
    final: bool = False  # the refinement seals the section


@dataclass
class ResolvedSection:
    name: str
    kind: SectionKind      # effective kind in the resolved skill
    title: str
    content: str
    sources: list[Contribution] = field(default_factory=list)
    declared: SectionKind = SectionKind.FINAL  # kind given by the declaring skill

    @property
    def filled(self) -> bool:
        return self.kind != SectionKind.ABSTRACT

    @property
    def sealed_by(self):
        """Skill whose refinement made the section final, if any."""
        return next((c.skill for c in self.sources if c.final), None)


_PAST = {"declares": "declared", "implements": "implemented",
         "overrides": "overridden", "extends": "extended"}


def provenance_trail(sec: ResolvedSection, show=str) -> str:
    """'declared abstract by a, implemented by b': who gave the section its
    content and kind; show renders a skill name (e.g. as a link)."""
    out = []
    for c in sec.sources:
        verb = _PAST[c.action]
        if c.action == "declares" and sec.declared != sec.kind:
            verb += f" {sec.declared.value}"
        elif c.final:
            verb += " and sealed"
        out.append(f"{verb} by {show(c.skill)}")
    return ", ".join(out)


@dataclass
class ResolvedSkill:
    name: str
    description: str
    chain: list[str]  # root .. skill
    sections: list[ResolvedSection]
    metadata: dict

    def section(self, name: str):
        return next((s for s in self.sections if s.name == name), None)


_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z_][\w.-]*)\s*\}\}")


def effective_metadata(lib: Library, skill: str) -> dict:
    meta: dict = {}
    for s in reversed(lib.skill_ancestors(skill)):
        meta.update(lib.skills[s].metadata)
    return meta


def substitute(text: str, skill_name: str, meta: dict) -> str:
    def repl(m):
        key = m.group(1)
        if key == "name":
            return skill_name
        if key.startswith("meta.") and key[5:] in meta:
            return str(meta[key[5:]])
        return m.group(0)
    return _PLACEHOLDER.sub(repl, text)


def resolve(lib: Library, name: str) -> ResolvedSkill:
    chain = list(reversed(lib.skill_ancestors(name)))
    sections: list[ResolvedSection] = []
    for depth, sname in enumerate(chain):
        sk = lib.skills[sname]
        for ref in getattr(sk, "refinements", []):
            tgt = next((s for s in sections if s.name == ref.target), None)
            if tgt is None:
                continue  # reported by T3
            if ref.kind in (RefinementKind.IMPLEMENTS, RefinementKind.OVERRIDES):
                tgt.content = ref.content
            elif ref.kind == RefinementKind.EXTENDS:
                tgt.content = (tgt.content + "\n\n" + ref.content).strip()
            tgt.kind = SectionKind.FINAL if ref.final else SectionKind.DEFAULT
            tgt.sources.append(Contribution(sname, ref.kind.value, ref.final))
        for sec in getattr(sk, "sections", []):
            if any(s.name == sec.name for s in sections):
                continue  # redeclaration is reported by T3
            sections.append(ResolvedSection(sec.name, sec.kind, sec.title, sec.content,
                                            [Contribution(sname, "declares")], declared=sec.kind))
    meta = effective_metadata(lib, name)
    for s in sections:
        s.content = substitute(s.content, name, meta)
        s.title = substitute(s.title, name, meta)
    sk = lib.skills[name]
    return ResolvedSkill(name=name, description=substitute(sk.description, name, meta),
                         chain=chain, sections=sections, metadata=meta)
