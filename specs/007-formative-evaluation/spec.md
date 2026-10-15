# Feature Specification: Formative evaluation (E1–E3)

**Feature Branch**: `007-formative-evaluation`
**Created**: 2026-10-07
**Status**: Implemented
**Input**: "Evaluate the first design iteration. E1: can DEFT express the structuring conventions used in practice, and how much does re-modelling Spec Kit save? E2: does the checker catch the faults each constraint describes, and which binding configurations does it accept? E3: what does generation produce, and how much of it repeats? Every figure must come out of one script."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Expressiveness (E1) (Priority: P1)

**Acceptance Scenarios**:

1. **Given** Spec Kit and Superpowers pinned in `upstream/`, **When** `survey.py` runs,
   **Then** it counts the conventions they use (handoffs, Pre-Execution Checks, prose
   references between skills, embedded DOT graphs) and maps each of 14 conventions to
   DEFT as full, partial or none (`mapping.yaml`).
2. **Given** the ten Spec Kit commands, **When** `refactor_speckit.py` runs, **Then** it
   re-models them as one family whose shared sections become ancestor sections with
   slots, resolution reproduces all ten command bodies exactly, and the family checks clean.

### User Story 2 - Checkability (E2) (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the example library, **When** `mutate.py` applies every operator at every
   applicable location, **Then** each mutant is reported, under the intended
   constraint, and the share reported only under it is computed.
2. **Given** each workflow template, **When** `configurations.py` enumerates every
   binding of its variation points, **Then** it reports accepted and rejected
   configurations and the codes of the rejections.

### User Story 3 - Generation (E3) (Priority: P2)

**Acceptance Scenarios**:

1. **Given** the example library, **When** `measure.py` runs, **Then** it reports
   authored, imported and generated sizes in lines and tokens, the content repeated
   across generated skills, and `skills-ref` results.

### User Story 4 - One command (Priority: P1)

`python experiments/run_all.py` runs everything and writes `results/summary.md`; CI runs it.

## Requirements *(mandatory)*

- **FR-001**: Mutation operators MUST be derived from the constraints: at least one per S/C/WF rule.
- **FR-002**: Sizes MUST be reported in non-blank lines and in tokens (tiktoken `o200k_base`).
- **FR-003**: Results MUST be JSON per experiment plus a Markdown summary.
- **FR-004**: E2 MUST report the violations of the baseline (unmutated) library, so a
  mutant counts as killed only against a clean baseline (recorded: 0).

## Success Criteria *(first iteration; see 010 for the current figures)*

- **SC-001**: 19 operators; every mutant killed under its intended constraint (281 mutants in this iteration).
- **SC-002**: Spec Kit family round trip identical for 10/10 commands.
- **SC-003**: 15/15 generated skills pass `skills-ref`.
