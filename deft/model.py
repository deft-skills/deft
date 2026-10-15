"""DEFT metamodel.

Specialization package: Library, ArtifactType, Property, Skill, AtomicSkill,
Section, Refinement, Parameter, Resource, Origin.
Composition package: CompositeSkill, SkillNode, ControlNode, DataEdge,
ControlEdge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

MANY = -1  # upper bound '*'


class SectionKind(str, Enum):
    FINAL = "final"        # no descendant may refine it
    ABSTRACT = "abstract"  # no content; a concrete descendant must implement it
    DEFAULT = "default"    # content that descendants may override or extend


class RefinementKind(str, Enum):
    IMPLEMENTS = "implements"
    OVERRIDES = "overrides"
    EXTENDS = "extends"


class Direction(str, Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"  # an artifact the skill receives and updates in place

    @property
    def is_input(self) -> bool:
        return self in (Direction.IN, Direction.INOUT)

    @property
    def is_output(self) -> bool:
        return self in (Direction.OUT, Direction.INOUT)


class ResourceKind(str, Enum):
    SCRIPT = "script"
    REFERENCE = "reference"
    ASSET = "asset"


# Folder of a skill where each kind of resource lives (Agent Skills specification).
RESOURCE_FOLDER = {ResourceKind.SCRIPT: "scripts", ResourceKind.REFERENCE: "references",
                   ResourceKind.ASSET: "assets"}


class OriginMode(str, Enum):
    ADAPTED = "adapted"    # rewritten from upstream material
    IMPORTED = "imported"  # upstream text used verbatim (sections with a source file)


class ControlKind(str, Enum):
    DECISION = "decision"
    FINAL = "final"


class ControlEdgeKind(str, Enum):
    SEQUENCE = "sequence"
    INVOKES = "invokes"
    REPAIR = "repair"


# --------------------------------------------------------------------------
# Specialization package
# --------------------------------------------------------------------------

@dataclass
class Property:
    name: str
    type: str = "string"
    lower: int = 1
    upper: int = 1
    values: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ArtifactType:
    name: str
    parent: Optional[str] = None
    abstract: bool = False
    description: str = ""
    properties: list[Property] = field(default_factory=list)


@dataclass
class Section:
    name: str
    kind: SectionKind
    title: str = ""
    content: str = ""
    source: Optional[str] = None  # file the content was read from, if any


@dataclass
class Refinement:
    kind: RefinementKind
    target: str
    content: str
    source: Optional[str] = None
    final: bool = False  # seals the section: descendants may not refine it again


@dataclass
class Parameter:
    name: str
    direction: Direction
    type: str
    lower: int = 1
    upper: int = 1
    description: str = ""

    @property
    def mandatory(self) -> bool:
        return self.lower > 0


@dataclass
class Resource:
    path: str
    kind: ResourceKind
    source: str  # file relative to the library root


@dataclass
class Origin:
    """Provenance of third-party material in a skill.

    A skill authored from scratch has no origin."""
    repo: str
    path: str
    commit: str
    license: str
    mode: OriginMode = OriginMode.ADAPTED


@dataclass
class Skill:
    """What every skill has: a signature, contracts and the optional fields of
    the Agent Skills specification. An atomic skill adds a body of sections;
    a composite skill adds a graph of nodes."""
    name: str
    description: str
    parent: Optional[str] = None
    abstract: bool = False
    parameters: list[Parameter] = field(default_factory=list)
    pre: list[str] = field(default_factory=list)
    post: list[str] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)
    origin: list[Origin] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    license: Optional[str] = None
    compatibility: Optional[str] = None
    allowed_tools: Optional[str] = None
    family: str = ""
    file: str = ""

    def param(self, name: str) -> Optional[Parameter]:
        return next((p for p in self.parameters if p.name == name), None)


@dataclass
class AtomicSkill(Skill):
    sections: list[Section] = field(default_factory=list)
    refinements: list[Refinement] = field(default_factory=list)


# --------------------------------------------------------------------------
# Composition package
# --------------------------------------------------------------------------

@dataclass
class SkillNode:
    name: str
    role: str
    bind: Optional[str] = None

    @property
    def effective(self) -> str:
        """Skill that performs the step: the binding, or the role itself."""
        return self.bind or self.role


@dataclass
class ControlNode:
    name: str
    kind: ControlKind


@dataclass
class Port:
    node: str  # node name, or "self" for the composite's own parameters
    param: str

    def __str__(self) -> str:
        return f"{self.node}.{self.param}"


@dataclass
class DataEdge:
    source: Port
    target: Port


@dataclass
class ControlEdge:
    kind: ControlEdgeKind
    source: str
    target: str
    guard: Optional[str] = None
    bound: Optional[int] = None
    carries: Optional[DataEdge] = None  # repair payload


@dataclass
class CompositeSkill(Skill):
    nodes: list = field(default_factory=list)  # SkillNode | ControlNode
    data: list[DataEdge] = field(default_factory=list)
    control: list[ControlEdge] = field(default_factory=list)

    def node(self, name: str):
        return next((n for n in self.nodes if n.name == name), None)

    def skill_nodes(self) -> list[SkillNode]:
        return [n for n in self.nodes if isinstance(n, SkillNode)]


# --------------------------------------------------------------------------
# Library
# --------------------------------------------------------------------------

@dataclass
class Library:
    name: str
    root: str = ""
    types: dict[str, ArtifactType] = field(default_factory=dict)
    skills: dict[str, Skill] = field(default_factory=dict)
    license: Optional[str] = None  # default licence of the library's skills
    license_files: dict[str, str] = field(default_factory=dict)  # repo -> path

    # -- hierarchy helpers (cycle-safe) -----------------------------------
    def _chain(self, name: str, table: dict) -> list[str]:
        chain, seen = [], set()
        cur = name
        while cur is not None and cur in table and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            cur = table[cur].parent
        return chain

    def type_ancestors(self, name: str) -> list[str]:
        """The type itself followed by its ancestors, nearest first."""
        return self._chain(name, self.types)

    def skill_ancestors(self, name: str) -> list[str]:
        """The skill itself followed by its ancestors, nearest first."""
        return self._chain(name, self.skills)

    def conforms_type(self, sub: str, sup: str) -> bool:
        """sub ⊑ sup on artifact types."""
        return sup in self.type_ancestors(sub)

    def conforms_skill(self, sub: str, sup: str) -> bool:
        """sub ⊑ sup on skills."""
        return sup in self.skill_ancestors(sub)

    def effective_property(self, type_name: str, name: str) -> Optional[Property]:
        """Nearest declaration of a property along the type hierarchy."""
        for t in self.type_ancestors(type_name):
            p = next((x for x in self.types[t].properties if x.name == name), None)
            if p is not None:
                return p
        return None

    def effective_properties(self, type_name: str) -> list[Property]:
        """All properties of a type, root first; the nearest declaration wins."""
        props: dict[str, Property] = {}
        for t in reversed(self.type_ancestors(type_name)):
            for p in self.types[t].properties:
                props[p.name] = p
        return list(props.values())

    def effective_param(self, skill: str, name: str) -> Optional[Parameter]:
        """Nearest declaration of a parameter along the hierarchy."""
        for s in self.skill_ancestors(skill):
            p = self.skills[s].param(name)
            if p is not None:
                return p
        return None

    def effective_params(self, skill: str) -> dict[str, Parameter]:
        params: dict[str, Parameter] = {}
        for s in reversed(self.skill_ancestors(skill)):
            for p in self.skills[s].parameters:
                params[p.name] = p
        return params

    def effective_attribute(self, skill: str, attr: str):
        """Nearest value of an optional field (license, compatibility,
        allowed_tools) along the hierarchy; the library's licence by default."""
        for s in self.skill_ancestors(skill):
            value = getattr(self.skills[s], attr, None)
            if value:
                return value
        return self.license if attr == "license" else None

    def effective_conditions(self, skill: str) -> tuple[list[str], list[str]]:
        """Inherited pre- and postconditions; descendants add (strengthen)."""
        pre, post = [], []
        for s in reversed(self.skill_ancestors(skill)):
            pre += [c for c in self.skills[s].pre if c not in pre]
            post += [c for c in self.skills[s].post if c not in post]
        return pre, post
