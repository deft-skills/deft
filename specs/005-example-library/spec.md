# Feature Specification: Example library (running example)

**Feature Branch**: `005-example-library`
**Created**: 2026-10-07
**Status**: Implemented
**Input**: "Build a realistic skill library for a spec-driven process that delivers a feature request in an existing system. Reuse public skills (Spec Kit, Superpowers, anthropics/skills) instead of writing everything from scratch. It must exercise every metamodel concept and contain at least one binding that is valid per hierarchy but ill-typed in the workflow."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Requirements family (Priority: P1)

`specify-requirements` (abstract) adapts Spec Kit *specify* and *clarify*: final
`elicit`, `clarify`, `record`; abstract `structure`; default `validate`.
`specify-functional` › `user-stories`, `ears`; `specify-quality` › `volere`, `iso25010`.

**Acceptance Scenarios**:

1. **Given** `ears`, **Then** it overrides `validate`; `user-stories` and `volere` extend it.
2. **Given** `iso25010`, **Then** its output type `ISO25010Requirement` is a
   `QualityRequirement` but not a `MeasurableQualityRequirement` (metric optional).

### User Story 2 - Planning, implementation, verification, support (Priority: P1)

- `plan-feature` adapts Spec Kit *plan*, *tasks* and Superpowers *writing-plans*.
- `execute-plan` (abstract) adapts the Superpowers *executing-plans* and
  *subagent-driven-development* skills; its variants are `execute-plan-inline` and
  `execute-plan-subagents`. `test-driven-development` is imported verbatim.
- `generate-tests` › `acceptance-tests` (`acceptance-gherkin`, `acceptance-playwright`),
  `performance-tests`. Only `acceptance-playwright` adapts anthropics/skills
  *webapp-testing*. Acceptance tests narrow their input to `UserStory`; performance
  tests to `MeasurableQualityRequirement`.
- `systematic-debugging` imported; `quantify-quality` authored as an adapter from
  `ISO25010Requirement` to measurable requirements.

### User Story 3 - Workflows (Priority: P1)

- `deliver-feature`: specify (functional ‖ quality) → plan → implement (invokes TDD)
  → verify (acceptance ‖ performance) → verdict → [fail] debug → repair (≤ 3) → implement.
- `deliver-feature-iso`: the same with `iso25010` and the `quantify-quality` adapter.

**Acceptance Scenarios**:

1. **Given** both workflows, **Then** `deft check` reports 0 violations.
2. **Given** `functional` bound to `ears`, **Then** C2 rejects the edge to `acceptance`.
3. **Given** `quality` bound to `iso25010` in `deliver-feature`, **Then** C2 rejects the edge to `performance`.

## Requirements *(mandatory)*

- **FR-001**: 14 artifact types in `models/types/artifacts.yaml`.
- **FR-002**: 21 skills (6 abstract) in five family files and two workflow files.
- **FR-003**: Every adapted or imported skill declares an `Origin` with repo, path, commit, licence and mode.
- **FR-004**: Imported text is read from `upstream/` with `source:`, never pasted.
- **FR-005**: The library declares the licence files of its upstream libraries.

## Success Criteria *(mandatory)*

- **SC-001**: `deft check models` → `14 types, 21 skills: 0 violation(s)`.
- **SC-002**: 15 skills generated, all valid.
- **SC-003**: Six skills adapt or import ten upstream skills or commands
  (`specify-requirements` 2, `plan-feature` 3, `execute-plan` 2,
  `test-driven-development` 1, `systematic-debugging` 1, `acceptance-playwright` 1).
