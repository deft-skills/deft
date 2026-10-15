# Data Model: Metamodel core (first iteration)

## Specialization package

| Entity | Attributes | Relations |
|---|---|---|
| Library | name, root | types: ArtifactType [*], skills: Skill [*], license_files |
| ArtifactType | name, abstract, description | parent: ArtifactType [0..1], properties: Property [*] |
| Property | name, type (default `string`), lower, upper, values, description | — |
| Skill | name, description, abstract, pre [*], post [*], metadata, family, file | parent: Skill [0..1]; sections: Section [*]; refinements: Refinement [*]; parameters: Parameter [*]; resources: Resource [*]; origin: Origin [*] |
| Section | name, kind ∈ {fixed, abstract, hook}, title, content, source | — |
| Refinement | kind ∈ {implements, overrides, extends}, target, content, source | target names an inherited Section |
| Parameter | name, direction ∈ {in, out}, type, lower, upper, description | type names an ArtifactType |
| Resource | path, kind ∈ {script, reference, asset}, source | — |
| Origin | repo, path, commit, license, mode ∈ {adapted, imported} | — |

## Composition package

| Entity | Attributes | Relations |
|---|---|---|
| CompositeSkill | (all of Skill) | nodes: SkillNode \| ControlNode [*]; data: DataEdge [*]; control: ControlEdge [*] |
| SkillNode | id, role, bind | role and bind name Skills; effective skill = bind or role |
| ControlNode | id, kind ∈ {decision, final} | — |
| Port | node (id or `self`), param | — |
| DataEdge | — | source: Port, target: Port |
| ControlEdge | kind ∈ {sequence, invokes, repair}, guard, bound | source, target: node ids; carries: DataEdge [0..1] |

## Derived operations (on Library)

- `type_ancestors(t)`, `skill_ancestors(s)`: the element and its ancestors, nearest first, cycle-safe.
- `conforms_type(a, b)`, `conforms_skill(a, b)`: `a ⊑ b`.
- `effective_property`, `effective_properties`, `effective_param`, `effective_params`: nearest declaration wins.
- `effective_conditions(s)`: pre- and postconditions accumulated along the chain.

## Multiplicity encoding

`upper = -1` (`MANY`) encodes `*`. A parameter is mandatory when `lower > 0`.
