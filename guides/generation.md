# Generating skills

`deft generate LIB --out DIR` writes one folder per concrete skill and per
executable workflow (every node bound to a concrete skill). Abstract skills are
not generated. Generation refuses to run on a library with violations unless
`--force` is given.

## Skills

The resolved skill is computed from the root of its lineage down: the root's
sections are taken in order, each descendant applies its refinements and adds
its new sections, and every change is recorded. The `SKILL.md` contains:

- frontmatter with the specification's fields (`name`, `description`,
  `license`, and `compatibility` and `allowed-tools` when the lineage declares
  them) and, under `metadata`: `deft-version`, `deft-lineage`, `deft-inputs`,
  `deft-outputs`, `deft-updates` (the `inout` parameters) and `deft-origin`;
- a title from `metadata.title`, or the name;
- **Inputs and outputs**: every parameter with its type, multiplicity and the
  properties of its artifact type (inherited properties first); `inout`
  parameters are listed as updated in place;
- **Before you start**: the inherited and own preconditions;
- the resolved sections, each followed by an HTML comment with its effective
  kind and provenance, such as `<!-- deft: default section 'structure'; declared
  abstract by specify-requirements, implemented by volere -->` (omit with
  `--no-provenance`);
- **Done when**: the inherited and own postconditions.

Resources bundled by the skill or by an ancestor are copied (the nearest
declaration wins). Licence files of the repositories named in the lineage's
`origin` are copied as `LICENSE-<project>.txt`, and the `license` field says so.

## Workflows

A workflow's `SKILL.md` lists its steps in an order compatible with all data,
sequence and invokes edges. Each step names the skill to load, where each input
comes from, and what it produces. Invoked skills are listed inside their caller.
Decisions list their guarded exits, and the repair loop states its bound and
what to do when the bound is reached. `metadata.deft-requires` lists every skill
the workflow needs, and `references/workflow.mmd` holds the graph in Mermaid.

## Validation

Every generated folder passes the reference validator of the specification
(`skills-ref`), which the tests and `experiments/e3_generation/measure.py` run.
