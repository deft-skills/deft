# Experiments

All scripts read the models under `models/` and the pinned copies under
`upstream/`, and write to `results/`. Run everything with:

```bash
python experiments/run_all.py
```

| Script | Criterion | Output |
|---|---|---|
| `e1_expressiveness/survey.py` | Expressiveness: structuring conventions observed in spec-kit and superpowers, and their DEFT representation (`mapping.yaml`) | `results/e1_survey.json` |
| `e1_expressiveness/refactor_speckit.py` | Expressiveness: the ten spec-kit commands re-modelled automatically as one DEFT family; round trip against the upstream text | `results/e1_speckit_refactoring.json`, `e1_expressiveness/speckit-model/` |
| `e2_checkability/mutate.py` | Checkability: 21 mutation operators seed one fault each, at every applicable location; detection per constraint | `results/e2_mutation.json` |
| `e2_checkability/configurations.py` | Checkability: every binding of the two workflow templates, accepted or rejected | `results/e2_configurations.json` |
| `c5_contracts/obligations.py` | C5 contract obligations of the workflows, for review; `review.yaml` records the manual review | `results/c5_obligations.{json,md}` |
| `e3_generation/measure.py` | Generated skills: sizes, repeated content, `skills-ref` validation | `results/e3_generation.json` |

`results/summary.md` collects the figures reported in the paper.

Sizes are reported in non-blank lines and in tokens. Tokens are counted with
tiktoken's `o200k_base` encoding as a stand-in for the tokenizers of current models
(ratios between texts depend little on the tokenizer); the encoding is downloaded
once on first use. These sizes measure what people author and maintain: the
resolved skills that agents read are the same with or without DEFT.

## Mutation operators

| Constraint | Operator | Fault |
|---|---|---|
| S1 | skill-cycle, type-cycle | a root becomes the child of one of its descendants |
| S2 | drop-implementation | a concrete skill loses an `implements` refinement |
| S3 | refine-final-section | a descendant overrides an inherited final section |
| S3 | refine-sealed-section | a refinement is sealed (`final: true`) and a child overrides the section again |
| S3 | swap-refinement-kind | `implements` and `overrides` are swapped |
| S3 | redeclare-inherited-section | a descendant redeclares an inherited section |
| S4 | widen-parameter-type | a redeclared parameter gets a type outside the inherited one |
| S4 | flip-parameter-direction | a redeclared parameter changes direction |
| S4 | widen-property-multiplicity | a subtype redeclares an inherited property with a looser multiplicity |
| WF | cross-kind-parent | a workflow specializes an atomic skill, or a root atomic skill a workflow |
| WF | mismatch-resource-kind | a bundled resource is declared with a kind that does not match its folder |
| WF | flip-origin-mode | an origin flips between `adapted` and `imported`, so it disagrees with the content |
| C1 | bind-abstract-skill | a node is bound to an abstract skill of its role's family |
| C1 | bind-unrelated-skill | a node is bound to a concrete skill outside its role's family |
| C2 | redirect-ill-typed-edge | a data edge takes its value from an output of a non-conforming type |
| C3 | drop-mandatory-input-edge | the only edge feeding a mandatory input is removed |
| C4 | unbound-repair-edge | a repair edge loses its iteration bound |
| C4 | repair-as-sequence | a repair edge becomes a sequence edge (cycle) |
| C4 | back-edge | a sequence edge goes back to a data predecessor (cycle) |
| C4 | reach-invoked-node | another node reaches an invoked node by a sequence edge |

The operators are derived from the constraints, so the experiment shows that
the checks are complete with respect to the faults each constraint describes,
not how often such faults occur in practice.

## C5 review by LLM judges and people

C5 relates natural-language conditions, so it is reviewed rather than decided.
`c5_contracts/review.yaml` records the reference review: the first version of the
models had three contract gaps, fixed since. Independent reviewers repeat that review
blind. A second reviewer and three LLM judges did so; where they disagreed with the
reference, two conditions were improved in the models (round 3 of `review.yaml`).
The items keep the conditions as they were reviewed, so the recorded answers stay
valid:

| Script | Does |
|---|---|
| `c5_contracts/items.py` | Rebuilds the first version of the models and lists the 16 obligations of `deliver-feature` before and after the fixes, shuffled, with the reference verdicts (`results/c5_items.json`) |
| `c5_contracts/judge.py` | Asks LLM judges (Anthropic, OpenAI, Google) with the same instructions as people (`results/c5_judges.json`) |
| `c5_contracts/make_sheet.py` | Builds `c5_contracts/human/c5-review-sheet.html`, a self-contained page for a human reviewer (see `c5_contracts/human/README.md`) |
| `c5_contracts/analyse.py` | Agreement of every reviewer with the reference and with each other: accuracy, gaps found, false alarms, Cohen's kappa (`results/c5_agreement.{json,md}`) |

The judges need API keys: copy `.env.example` to `.env` (never committed) and fill
in the keys and models; providers without a key are skipped. Answers are cached in
`results/c5_judge_cache.json`, so a rerun reproduces them without keys.

```bash
python experiments/c5_contracts/items.py
python experiments/c5_contracts/judge.py
python experiments/c5_contracts/analyse.py
```

## Agent run (E4)

Running the generated workflow with a real coding agent is a usage example of DEFT
rather than an experiment script: see [`examples/account-service`](../examples/account-service/)
for the system, the feature request, the preparation script and the checker of the
produced artifacts.
