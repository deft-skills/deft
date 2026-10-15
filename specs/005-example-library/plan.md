# Implementation Plan: Example library

**Branch**: `005-example-library` | **Spec**: [spec.md](spec.md)

## Summary

Model a feature-delivery process as five skill families, two workflows and 14
artifact types, reusing pinned upstream skills.

## Constitution Check

- IV. Reference, do not copy: imported sections use `source:`; origins pinned by commit. PASS
- II. Check before execution: the library must check clean, and the two documented
  wrong bindings must fail (C2). PASS

## Project Structure

```text
models/
├── library.yaml            # name, default licence, upstream licence files
├── types/artifacts.yaml    # 14 types
├── skills/
│   ├── requirements.yaml   # specify-requirements family (7 skills)
│   ├── planning.yaml       # plan-feature
│   ├── implementation.yaml # execute-plan family, test-driven-development
│   ├── verification.yaml   # generate-tests family (5 skills)
│   └── debugging.yaml      # systematic-debugging, quantify-quality
└── workflows/
    ├── deliver-feature.yaml
    └── deliver-feature-iso.yaml
```

## Design decisions

1. **Type hierarchy drives the variation.** `Requirement` › `FunctionalRequirement` ›
   {`UserStory`, `EARSRequirement`}; `QualityRequirement` ›
   {`MeasurableQualityRequirement` › `VolereRequirement`, `ISO25010Requirement`}.
   The ISO type is deliberately not measurable, so binding it to performance tests fails.
2. **Adapt vs. import.** Procedures that need DEFT's structure are adapted (rewritten);
   self-contained procedures (TDD, debugging) are imported verbatim.
3. **Two workflows** show that the same template accepts different bindings, and that
   the ISO variant needs an adapter node.
