# Implementation Plan: Formative evaluation (E1–E3)

**Branch**: `007-formative-evaluation` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

One script per measurement, a shared helper module, and a runner that writes JSON per
experiment and a Markdown summary of the figures reported in the paper.

## Technical Context

**Language/Version**: Python 3.11+
**Dependencies**: `deft` itself; `tiktoken` (`o200k_base`) and `skills-ref` from the `test` extras
**Inputs**: `models/`, `upstream/` (pinned Spec Kit and Superpowers)
**Outputs**: `experiments/results/*.json`, `experiments/results/summary.md`

## Constitution Check

- V. Reproducible evidence: every figure comes from `run_all.py`; CI runs it. PASS
- VI. Small and dependency-light: evaluation dependencies stay in optional extras. PASS

## Project Structure

```text
experiments/
├── common.py
├── run_all.py
├── e1_expressiveness/   # survey.py, mapping.yaml, refactor_speckit.py, speckit-model/
├── e2_checkability/     # mutate.py, configurations.py
├── e3_generation/       # measure.py
└── results/
```

## Design decisions

1. **Mutation operators derived from the constraints**, applied at every location, so
   detection can be reported per constraint (killed, intended, exclusive).
2. **Configurations enumerated, not sampled**: every binding of every variation point.
3. **Spec Kit re-modelled by script**, with an exact round-trip check (see research.md).
4. **Measure what authors maintain**, not what agents read: resolved skills are the same
   with or without DEFT.
