"""Load a DEFT library from a directory of YAML model files.

Layout:
    <root>/library.yaml        name of the library and optional includes
    <root>/types/*.yaml        artifact types
    <root>/skills/*.yaml       skills (one family per file)
    <root>/workflows/*.yaml    composite skills
"""
from __future__ import annotations

import glob
import os
from typing import Any

import yaml

from .model import (MANY, ArtifactType, AtomicSkill, CompositeSkill, ControlEdge,
                    ControlEdgeKind, ControlKind, ControlNode, DataEdge,
                    Direction, Library, Origin, OriginMode, Parameter, Port, Property,
                    Refinement, RefinementKind, Resource, ResourceKind,
                    Section, SectionKind, SkillNode)


class ModelError(Exception):
    """Raised when a model file is not well-formed (schema level)."""


def _upper(v: Any) -> int:
    if v in ("*", "many", None):
        return MANY
    return int(v)


def _mult(d: dict, default_lower=1, default_upper=1) -> tuple[int, int]:
    lower = int(d.get("lower", default_lower))
    upper = _upper(d.get("upper", default_upper)) if "upper" in d else default_upper
    return lower, upper


def _require(d: dict, key: str, where: str):
    if key not in d:
        raise ModelError(f"{where}: missing '{key}'")
    return d[key]


def _parse_type(d: dict, where: str) -> ArtifactType:
    parent = d.get("parent")
    if isinstance(parent, list):
        raise ModelError(f"{where}: a type has at most one parent (S1)")
    props = []
    for p in d.get("properties", []):
        lo, up = _mult(p)
        props.append(Property(name=_require(p, "name", where), type=p.get("type", "string"),
                              lower=lo, upper=up, values=list(p.get("values", [])),
                              description=p.get("description", "")))
    return ArtifactType(name=_require(d, "name", where), parent=parent,
                        abstract=bool(d.get("abstract", False)),
                        description=d.get("description", ""), properties=props)


def _parse_port(s: str, where: str) -> Port:
    if not isinstance(s, str) or "." not in s:
        raise ModelError(f"{where}: port '{s}' must be 'node.param'")
    node, param = s.split(".", 1)
    return Port(node, param)


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def extract_section(text: str, heading: str | None) -> str:
    """Body of a Markdown file, or of one '## heading' section of it."""
    body = strip_frontmatter(text)
    if heading is None:
        return body.rstrip()
    out, inside = [], False
    for line in body.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip() == heading
            continue
        if inside:
            out.append(line)
    if not inside and not out:
        raise ModelError(f"heading '{heading}' not found")
    return "\n".join(out).strip()


def demote(text: str) -> str:
    """Drop a leading H1 and shift headings one level down (## -> ###)."""
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    out, fence = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and line.startswith("#"):
            line = "#" + line
        out.append(line)
    return "\n".join(out).strip()


def _content(s: dict, root: str, where: str) -> str:
    if "source" in s:
        path = os.path.join(root, s["source"])
        if not os.path.exists(path):
            raise ModelError(f"{where}: source '{s['source']}' not found")
        with open(path, encoding="utf-8") as fh:
            text = extract_section(fh.read(), s.get("heading"))
        return demote(text) if s.get("demote") else text
    return (s.get("content") or "").rstrip()


def _parse_body(d: dict, where: str, root: str = "") -> dict:
    sections = [Section(name=_require(s, "name", where), kind=SectionKind(s.get("kind", "final")),
                        title=s.get("title", ""), content=_content(s, root, where),
                        source=s.get("source"))
                for s in d.get("sections", [])]
    refinements = [Refinement(kind=RefinementKind(_require(r, "kind", where)),
                              target=_require(r, "target", where),
                              content=_content(r, root, where), source=r.get("source"),
                              final=bool(r.get("final", False)))
                   for r in d.get("refinements", [])]
    return dict(sections=sections, refinements=refinements)


def _parse_skill_common(d: dict, where: str, root: str = "") -> dict:
    parent = d.get("parent")
    if isinstance(parent, list):
        raise ModelError(f"{where}: a skill has at most one parent (S1)")
    params = []
    for p in d.get("parameters", []):
        lo, up = _mult(p)
        params.append(Parameter(name=_require(p, "name", where),
                                direction=Direction(_require(p, "direction", where)),
                                type=_require(p, "type", where), lower=lo, upper=up,
                                description=p.get("description", "")))
    resources = [Resource(path=_require(r, "path", where), kind=ResourceKind(r.get("kind", "reference")),
                          source=_require(r, "source", where))
                 for r in d.get("resources", [])]
    origin = [Origin(repo=o["repo"], path=o["path"], commit=o["commit"], license=o["license"],
                     mode=OriginMode(o.get("mode", "adapted")))
              for o in d.get("origin", [])]
    return dict(name=_require(d, "name", where), description=_require(d, "description", where),
                parent=parent, abstract=bool(d.get("abstract", False)),
                parameters=params, pre=list(d.get("pre", [])),
                post=list(d.get("post", [])), resources=resources, origin=origin,
                metadata=dict(d.get("metadata", {})), license=d.get("license"),
                compatibility=d.get("compatibility"), allowed_tools=d.get("allowed-tools"))


def _parse_composite(d: dict, where: str, root: str = "") -> CompositeSkill:
    for key in ("sections", "refinements"):
        if key in d:
            raise ModelError(f"{where}: composite skill '{d.get('name')}' has no {key}; its body is its graph")
    common = _parse_skill_common(d, where, root)
    nodes = []
    for n in d.get("nodes", []):
        nid = _require(n, "name", where)
        if "kind" in n:
            nodes.append(ControlNode(nid, ControlKind(n["kind"])))
        else:
            nodes.append(SkillNode(nid, role=_require(n, "role", where), bind=n.get("bind")))
    data = [DataEdge(_parse_port(_require(e, "from", where), where), _parse_port(_require(e, "to", where), where))
            for e in d.get("data", [])]
    control = []
    for e in d.get("control", []):
        carries = None
        if "carries" in e:
            c = e["carries"]
            carries = DataEdge(_parse_port(c["from"], where), _parse_port(c["to"], where))
        control.append(ControlEdge(kind=ControlEdgeKind(_require(e, "kind", where)),
                                   source=_require(e, "from", where), target=_require(e, "to", where),
                                   guard=e.get("guard"), bound=e.get("bound"), carries=carries))
    return CompositeSkill(**common, nodes=nodes, data=data, control=control)


def library_from_dict(docs: list[tuple[str, dict]], name: str = "library", root: str = "") -> Library:
    """Build a library from (filename, yaml-document) pairs."""
    lib = Library(name=name, root=root)
    for fname, doc in docs:
        if not doc:
            continue
        family = doc.get("family", os.path.splitext(os.path.basename(fname))[0])
        for t in doc.get("types", []):
            at = _parse_type(t, fname)
            if at.name in lib.types:
                raise ModelError(f"{fname}: duplicate type '{at.name}'")
            lib.types[at.name] = at
        for s in doc.get("skills", []):
            sk = (_parse_composite(s, fname, root) if s.get("composite")
                  else AtomicSkill(**_parse_skill_common(s, fname, root), **_parse_body(s, fname, root)))
            if sk.name in lib.skills:
                raise ModelError(f"{fname}: duplicate skill '{sk.name}'")
            sk.family, sk.file = family, fname
            lib.skills[sk.name] = sk
    return lib


def _read_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_library(root: str, extra: list[str] | None = None) -> Library:
    """Load every model file under root (and optional extra files)."""
    root = os.path.abspath(root)
    meta_path = os.path.join(root, "library.yaml")
    meta = _read_yaml(meta_path) if os.path.exists(meta_path) else {}
    files = []
    for sub in ("types", "skills", "workflows"):
        files += sorted(glob.glob(os.path.join(root, sub, "*.yaml")))
    for inc in meta.get("include", []):
        files += sorted(glob.glob(os.path.join(root, inc)))
    files += list(extra or [])
    docs = [(os.path.relpath(f, root).replace("\\", "/"), _read_yaml(f)) for f in files]
    lib = library_from_dict(docs, name=meta.get("name", os.path.basename(root)), root=root)
    lib.license = meta.get("license")
    lib.license_files = dict(meta.get("licenses", {}))
    return lib


def read_resource(lib: Library, res: Resource) -> str:
    with open(os.path.join(lib.root, res.source), encoding="utf-8") as fh:
        return fh.read()
