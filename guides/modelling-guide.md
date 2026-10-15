# Writing models

This guide shows how to write a DEFT library. The running example under
`models/` follows it.

## 1. Library

```
models/
  library.yaml       # name; licence of the skills; licence files of third-party sources
  types/*.yaml       # artifact types
  skills/*.yaml      # skills, one family per file
  workflows/*.yaml   # composite skills
```

`library.yaml` names the library and, optionally, the licence of its generated
skills (a skill may declare its own `license`). It may also map repositories to
licence files: the generator copies the licence next to every skill whose lineage
names that repository as its origin.

```yaml
name: deft-feature-delivery
license: GPL-3.0-only
licenses:
  github/spec-kit: ../upstream/spec-kit/LICENSE
```

## 2. Artifact types

Artifact types describe what skills exchange. Each type has at most one parent; a
property has a multiplicity (`lower`, `upper`; `"*"` for many).

```yaml
types:
  - name: QualityRequirement
    parent: Requirement
    abstract: true
  - name: MeasurableQualityRequirement
    parent: QualityRequirement
    abstract: true
    properties:
      - {name: fitCriterion}            # required
  - name: ISO25010Requirement
    parent: QualityRequirement
    properties:
      - {name: metric, lower: 0}        # optional: not measurable by type
```

Put a property where its multiplicity holds for every descendant. A subtype may
redeclare an inherited property only to tighten its multiplicity (for example
`criteria [1..*]` to `[2..*]`); loosening it violates T4. The difference between a
mandatory fit criterion and an optional metric is what lets the checker reject
an ISO/IEC 25010 requirement upstream of a load test.

## 3. Skills

An atomic skill has a `description` (when to use it, as in the specification),
typed `parameters`, `pre` and `post` conditions, and `sections`.

```yaml
- name: specify-requirements
  abstract: true
  description: Use when a feature request must become testable requirements.
  parameters:
    - {name: request, direction: in, type: FeatureRequest}
    - {name: requirements, direction: out, type: Requirement, lower: 1, upper: "*"}
  post:
    - Every requirement has a unique id and names its source.
  sections:
    - {name: elicit, kind: final, title: Identify sources and stakeholders, content: "..."}
    - {name: structure, kind: abstract, title: Structure each requirement}
    - {name: validate, kind: default, title: Validate the requirements, content: "..."}
```

| Kind | Use it for | Descendants may |
|---|---|---|
| `final` (the default) | Procedure every member of the family must follow | nothing |
| `abstract` | Variation point without a sensible default | `implements` (concrete skills must) |
| `default` | Content that some members change | `overrides`, `extends` |

A parameter's `direction` is `in`, `out` or `inout`. Use `inout` for an artifact
the skill receives and updates in place, such as a code base or a specification it
revises: the generated skill tells the agent to update it rather than produce a new
one, and in workflows the parameter is both an input and an output.

The optional fields of the specification, `license`, `compatibility` and
`allowed-tools`, are written as in a `SKILL.md`; descendants inherit them unless
they redeclare them. `metadata` values are inherited key by key.

A specialization names its `parent`, redeclares parameters only to narrow
their type, and refines inherited sections:

```yaml
- name: volere
  parent: specify-quality
  description: Use when quality requirements must be Volere snow cards.
  parameters:
    - {name: requirements, direction: out, type: VolereRequirement, lower: 1, upper: "*"}
  refinements:
    - {kind: implements, target: structure, content: "..."}
    - {kind: extends, target: validate, content: "..."}
```

A refined section becomes `default` for the refining skill and its descendants,
so a further specialization may override or extend it again. To forbid that, seal
the section with `final: true` on the refinement:

```yaml
  refinements:
    - {kind: implements, target: structure, final: true, content: "..."}
```

A descendant may also declare new sections; they follow the inherited ones.
Conditions accumulate along the hierarchy: descendants add pre- and
postconditions.

### Placeholders

Section content may contain `{{name}}` (the resolved skill's name) and
`{{meta.<key>}}` (a `metadata` value of the resolved skill or of its nearest
ancestor that defines it). One section can then serve a family whose copies
differ only in names, as in the spec-kit re-model under
`experiments/e1_expressiveness/speckit-model/`.

### Reusing third-party skills

Record where material comes from with `origin`, and take content from a file
with `source` instead of copying it:

```yaml
- name: test-driven-development
  origin:
    - {repo: obra/superpowers, path: skills/test-driven-development/SKILL.md,
       commit: 8ca22db..., license: MIT, mode: imported}
  sections:
    - name: procedure
      kind: final
      source: ../upstream/superpowers/skills/test-driven-development/SKILL.md
      demote: true          # drop its title and shift headings one level down
```

Use `heading: <title>` to take a single `##` section of the file.

`mode` is `adapted` (the default: upstream material rewritten by the authors) or
`imported` (upstream text used verbatim through `source:`). The two must agree:
an imported origin requires at least one section read from a file, and a section
read from a file requires an imported origin. A skill written from scratch has
no `origin`. Imported content is refreshed by bumping the pinned commit and
regenerating; adapted content needs a person to review upstream changes.

### Bundled resources

```yaml
resources:
  - {path: scripts/with_server.py, kind: script, source: ../upstream/.../with_server.py}
```

`kind` is `script`, `reference` or `asset`, and `path` must start with the
matching folder of the specification: `scripts/`, `references/` or `assets/`.
Descendants inherit resources; the nearest declaration of a path wins.

## 4. Workflows

A composite skill declares its own parameters and conditions, and a graph
instead of sections. It may specialize another composite skill, but not an
atomic one.

```yaml
- name: deliver-feature
  composite: true
  parameters:
    - {name: request, direction: in, type: FeatureRequest}
    - {name: code, direction: out, type: SourceCode}
  nodes:
    - {name: functional, role: specify-functional, bind: user-stories}
    - {name: plan, role: plan-feature}
    - {name: verdict, kind: decision}
    - {name: done, kind: final}
  data:
    - {from: self.request, to: functional.request}
    - {from: functional.requirements, to: plan.requirements}
  control:
    - {kind: invokes, from: implement, to: tdd}
    - {kind: sequence, from: verdict, to: done, guard: every report has verdict pass}
    - {kind: repair, from: debug, to: implement, bound: 3,
       carries: {from: debug.diagnosis, to: implement.diagnosis}}
```

- `role` names the skill the step requires, usually abstract; `bind` names the
  specialization that performs it. Without `bind`, a node with an abstract role
  makes the workflow a template: it is checked, but not generated.
- Data edges connect `node.parameter` ports; `self.x` is a parameter of the
  workflow. Several edges may feed a many-valued input.
- A node is ready when all its mandatory inputs exist. Use `sequence` edges
  only where no data flows, or to leave a decision.
- `invokes` runs the target inside the source; the target may take mandatory
  inputs from the caller's parameters.
- `repair` returns to an earlier node and needs a `bound`; `carries` passes an
  artifact (typically a diagnosis) to an optional input of the target.

## 5. Check, review, generate

```bash
deft check models          # fix every violation before generating
deft obligations models    # review that guarantees entail preconditions (C5)
deft generate models --out skills
```
