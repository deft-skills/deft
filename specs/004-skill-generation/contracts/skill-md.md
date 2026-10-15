# Output contract: generated skill folder

```text
skills/<name>/
├── SKILL.md
├── LICENSE-<upstream>.txt     # one per upstream library the skill derives from
├── scripts/ references/ assets/   # resources of the skill and its ancestors
└── references/workflow.mmd    # workflows only
```

## Frontmatter

```yaml
---
name: <skill>
description: <resolved description>
license: GPL-3.0-only [ (includes third-party material; see LICENSE-*.txt)]
metadata:
  deft-version: 0.1.0
  deft-lineage: <root> > … > <skill>
  deft-inputs: '<param>: <Type> [<mult>]; …'
  deft-outputs: '<param>: <Type> [<mult>]; …'
  deft-origin: <repo>@<commit7> <path> (<licence>, <mode>); …   # if any, ancestors included
  deft-requires: <skill>, …                                  # workflows only
---
```

## Body (atomic skill)

1. `# <title>` (from `metadata.title`).
2. `## Inputs and outputs`: each parameter with its type, multiplicity, description and
   the fields of the type.
3. Preconditions and postconditions.
4. One `##` heading per resolved section, each preceded by a provenance comment.

## Body (workflow)

1. Coordination preamble (load each named skill when its step starts).
2. `## Inputs and outputs`.
3. `## Before you start`: the workflow preconditions.
4. `## Workflow`: `### Step N: <node>` in topological order, with the skill to load and
   the artifacts in and out; decision steps are marked `(decision)`; a final
   `### Repair loop` gives the repair edge and its bound.
5. `## Done when`: the workflow postconditions.
