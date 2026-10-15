# Implementation Plan: Metamodel iteration after review

**Branch**: `010-metamodel-iteration-2` | **Spec**: [spec.md](spec.md)

## Summary

Change the metamodel in all its forms at once (dataclasses, Ecore, OCL, diagrams,
guides), migrate the example models, extend checks, generator and mutation operators,
and regenerate every derived artifact.

## Technical Context

**Language/Version**: Python 3.11+ | **Dependencies**: none new
**Scope**: 99 files in one change (models, skills, results and docs are regenerated)

## Constitution Check

- III. One rule, three forms: every renamed kind and new rule updated in guide, OCL,
  code and tests in the same change. PASS
- V. Reproducible evidence: `skills/`, `results/` and `docs/` regenerated; figures in the
  paper change (281 → 311 mutants). PASS
- Constitution amended: *Last Amended* date set to this iteration.

## Migration

| Before | After |
|---|---|
| `kind: fixed` | `kind: final` |
| `kind: hook` | `kind: default` |
| `Skill.sections`, `Skill.refinements` | `AtomicSkill.sections`, `AtomicSkill.refinements` |
| node `id:` | node `name:` |
| — | `refinement.final: true` (sealing) |
| — | `direction: inout` |
| — | `license`, `compatibility`, `allowed-tools`; `library.license` |

## Design decisions

1. **Derived section kinds.** A refined section is `default` for further descendants,
   or `final` if the refinement seals it; S2 and S3 read the effective kind.
2. **Kind-preserving specialization.** An atomic skill specializes only atomic skills,
   a composite only composites (WF), so resolution and composition stay separate.
3. **Optional fields are inherited** like metadata, nearest declaration wins.
4. **Two new operators** cover the two new rules (sealing, cross-kind parent).
