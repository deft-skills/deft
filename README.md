# DEFT: a metamodel for agent skills

[Agent skills](https://agentskills.io) are folders of instructions, scripts and
resources that coding agents load on demand. The specification fixes a few metadata
fields and leaves skills unrelated, so libraries grow by copying, and pipelines of
skills are described in prose that nobody checks.

DEFT treats skill libraries as software:

- **Specialization**: skills form hierarchies. A parent holds the procedure every
  variant shares (final sections); variants fill its variation points (abstract
  sections) or change its defaults (default sections).
- **Composition**: skills form workflows whose steps exchange typed artifacts and
  declare pre- and postconditions.
- **Checks before execution**: hierarchies, bindings and data flow are validated before
  any agent runs. A variant that accepts a narrower input than its parent is fine in
  the hierarchy, but rejected where it is wired to an incompatible step.
- **Plain skills out**: every model generates standard `SKILL.md` folders that any
  compatible agent can use, with provenance and licences of reused material.

You write models, DEFT checks them, and DEFT generates skills. Agents only see the
generated skills.

---

## Get started

Requires Python 3.11 or later. Download the repository from
https://anonymous.4open.science/r/deft-A5CA/, unzip it, and run from its folder:

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[test]"
```

Check the example library, look at one resolved skill, and generate all of them:

```bash
deft check models                    # 14 types, 21 skills: 0 violation(s)
deft resolve models volere           # the SKILL.md an agent receives for 'volere'
deft generate models --out skills    # 15 skills, one folder each
```

---

## Learn DEFT step by step

### 1. Understand the metamodel

Read [The DEFT metamodel](guides/metamodel.md). Then open
[`models/skills/requirements.yaml`](models/skills/requirements.yaml) and follow one
family: `specify-requirements` (abstract: final elicitation and clarification, an
abstract `structure` section, a default `validate` section) and its specializations
`user-stories`, `ears`, `volere` and `iso25010`.

### 2. Write a model

Read [Writing models](guides/modelling-guide.md). As an exercise, add a new notation for
quality requirements. Planguage requirements are measurable, so they specialize
`MeasurableQualityRequirement`. In `models/types/artifacts.yaml`:

```yaml
  - name: PlanguageRequirement
    parent: MeasurableQualityRequirement
    properties:
      - {name: scale}
      - {name: meter}
```

and in `models/skills/requirements.yaml`:

```yaml
  - name: planguage
    parent: specify-quality
    description: Use when quality requirements must be written in Planguage.
    parameters:
      - {name: requirements, direction: out, type: PlanguageRequirement, lower: 1, upper: "*"}
    refinements:
      - kind: implements
        target: structure
        content: |
          Write each requirement with the Planguage keywords Tag, Gist, Scale,
          Meter, Must and Plan. ...
```

### 3. Validate it

Read [Validating models](guides/constraints.md) and run:

```bash
deft check models
```

Then bind your variant in `models/workflows/deliver-feature.yaml`
(`{name: quality, role: specify-quality, bind: planguage}`) and check again: it passes,
because a Planguage requirement is measurable and the performance tests accept it.
Bind `iso25010` instead and the check fails with a type error (C2): the metric of an
ISO/IEC 25010 requirement is optional. Undo the changes when you are done.

Review the contracts of a workflow, which DEFT lists but cannot decide:

```bash
deft obligations models --workflow deliver-feature
```

### 4. Generate the skills

Read [Generating skills](guides/generation.md), run `deft generate models --out skills`,
and compare [`skills/volere/SKILL.md`](skills/volere/SKILL.md) with its model: inherited
sections, provenance comments, inputs and outputs with their fields, conditions, and
the licence of the adapted material.

### 5. Use the skills with an agent

Read [Using generated skills](guides/using-skills.md), then run the complete example in
[`examples/account-service`](examples/account-service/): an agent delivers a feature
request (password reset) on a small existing service by following the
`deliver-feature` workflow, and a checker reports the artifacts, the traceability from
requirements to tests, and the test verdict.

### 6. Browse the catalogue

The website, published from [`docs/`](docs/), documents DEFT and browses every skill,
workflow and artifact type of the library. To rebuild it after changing the models or
the guides, and preview it locally:

```bash
python site/build.py                 # writes docs/
python -m http.server -d docs 8000   # http://localhost:8000
```

The [command-line reference](guides/cli.md) lists every `deft` command.

---

## The example library

A spec-driven process to deliver a feature request, built on public skills:

| Family | Skills | Built on |
|---|---|---|
| Requirements | `specify-requirements` › `specify-functional` (`user-stories`, `ears`), `specify-quality` (`volere`, `iso25010`) | [Spec Kit](https://github.com/github/spec-kit) *specify*, *clarify* (adapted) |
| Planning | `plan-feature` | Spec Kit *plan*, *tasks*; [Superpowers](https://github.com/obra/superpowers) *writing-plans* (adapted) |
| Implementation | `execute-plan` › `execute-plan-inline`, `execute-plan-subagents`; `test-driven-development` | Superpowers executors (adapted), TDD (imported) |
| Verification | `generate-tests` › `acceptance-tests` (`acceptance-gherkin`, `acceptance-playwright`), `performance-tests` | [anthropics/skills](https://github.com/anthropics/skills) *webapp-testing* (adapted) |
| Support | `systematic-debugging`, `quantify-quality` | Superpowers debugging (imported) |
| Workflows | `deliver-feature`, `deliver-feature-iso` | |

```
specify (functional ‖ quality) → plan → implement (invokes TDD)
  → verify (acceptance ‖ performance) → verdict → [fail] debug → repair (≤ 3) → implement
```

---

## Repository layout

| Path | Contents |
|---|---|
| [`guides/`](guides/) | Documentation (start with [guides/README.md](guides/README.md)) |
| [`docs/`](docs/) | The built website (generated with `python site/build.py`; do not edit) |
| [`deft/`](deft/) | The `deft` tool: loader, resolution, checks, generator, diagrams, CLI |
| [`metamodel/`](metamodel/) | The metamodel in Ecore and OCL, and diagrams |
| [`models/`](models/) | The example library |
| [`skills/`](skills/) | Skills generated from the example library |
| [`examples/`](examples/) | Runnable example with a coding agent |
| [`upstream/`](upstream/) | Pinned third-party skills the example library reuses, with their licences |
| [`site/`](site/) | Website generator |
| [`tests/`](tests/) | Tests of every check and of the generator |
| [`experiments/`](experiments/) | Research evaluation of DEFT (see below) |
| [`specs/`](specs/) | Specifications, plans and tasks from which DEFT was built (see [Use of generative AI](#use-of-generative-ai)) |

## Research evaluation

[`experiments/`](experiments/) contains the scripts and results of the formative
evaluation of DEFT reported in the accompanying paper: functional correctness,
functional completeness and maintainability. Run `python experiments/run_all.py`; [experiments/README.md](experiments/README.md)
describes each experiment.

## Contributing

DEFT is open source, and contributions are welcome. You can help in several ways:

- **Report a problem or propose an idea.** Open an issue. For a bug in the checker or the
  generator, include the smallest model that reproduces it and the output of
  `deft check`.
- **Add skills.** New skill families, workflows and artifact types go in `models/` as YAML
  (see [Writing models](guides/modelling-guide.md)). To reuse a third-party skill, pin it
  in `upstream/` with its licence, reference it through `origin` and `source` rather than
  copying it, and list it in [NOTICE](NOTICE).
- **Improve the tool.** The loader, checks, resolution and generator live in `deft/`. A
  new or changed constraint also needs a test in `tests/`, its OCL invariant in
  [`metamodel/deft.ocl`](metamodel/deft.ocl), and an update to
  [Validating models](guides/constraints.md).
- **Improve the documentation.** The guides are in `guides/`; the website is generated
  from them.

### Set up

Download the repository from https://anonymous.4open.science/r/deft-A5CA/, unzip it,
and run from its folder:

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[test]"
```

### Before you open a pull request

Run the same checks as the continuous integration:

```bash
python -m pytest                     # tests of every check and of the generator
deft check models                    # the example library has no violation
deft generate models --out skills    # regenerate the skills, commit the changes
python site/build.py --out docs      # regenerate the website, commit the changes
python experiments/run_all.py        # rerun the evaluation, commit changed results
```

Edit the models and the guides, never the generated files: `skills/` and `docs/` are
overwritten on every build, and the continuous integration fails if they are out of date.
If your change alters the results in `experiments/results/`, say so in the pull request.

Contributions are accepted under the GNU General Public License v3.0, and third-party
material must have a compatible licence. You may use AI assistants, provided you review
the result and say so in the pull request, as we do in this repository (see below).

## Use of generative AI

We designed the DEFT metamodel, its constraints and the research. We then built DEFT
with an LLM-based coding agent, using spec-driven development with
[Spec Kit](https://github.com/github/spec-kit). For each feature, we wrote what it had to
do, and the agent turned it into a specification, a plan and tasks, which we reviewed and
edited. The agent then implemented the tasks. We followed its work, and checked and
edited everything it produced before accepting it.

You can audit the process. [`specs/`](specs/) holds the specification, plan and tasks of
each of the ten features, in the order we built them, and
[`.specify/memory/constitution.md`](.specify/memory/constitution.md) holds the rules that
every feature had to follow.

The example skills illustrate DEFT. DEFT does not claim or evaluate how good they are as
skills.

## Licence

GNU General Public License v3.0 (see [LICENSE](LICENSE)). Third-party material under
`upstream/` and in the generated skills that reuse it keeps its original licence; see
[NOTICE](NOTICE).
