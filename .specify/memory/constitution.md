# DEFT Constitution

## Core Principles

### I. Models in, standard skills out
Authors write models; agents only ever see standard `SKILL.md` folders that pass the
Agent Skills reference validator (`skills-ref`). DEFT adds no runtime, no new file
format for agents and no agent-specific extension.

### II. Check before execution
Every structural and type rule that can be decided is checked by `deft check`
before any agent runs. Rules that cannot be decided (natural-language contracts)
are listed as obligations for people to review, never silently accepted.

### III. One rule, three forms
Every constraint exists as (a) a row in `guides/constraints.md`, (b) an OCL
invariant in `metamodel/deft.ocl`, and (c) a check in `deft/check.py` with a test in
`tests/`. A change to one form is incomplete until the other two follow.

### IV. Reference, do not copy
Third-party skills are pinned by commit under `upstream/`, referenced through
`origin` and `source`, and their licences travel with every generated skill that
derives from them.

### V. Reproducible evidence
Every figure reported in the paper is produced by `python experiments/run_all.py`
from the models and the pinned upstream copies, and collected in
`experiments/results/summary.md`. CI fails when generated skills or the website are
out of date.

### VI. Small and dependency-light
Python 3.11+, PyYAML as the only runtime dependency. Test-only dependencies
(`pytest`, `skills-ref`, `tiktoken`) stay optional.

## Governance

The authors review every specification, plan and generated artifact produced with
the coding agent before it is merged. Amendments to this constitution require a
note in the affected feature's `plan.md` under *Constitution Check*.