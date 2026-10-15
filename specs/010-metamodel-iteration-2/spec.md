# Feature Specification: Metamodel iteration after review

**Feature Branch**: `010-metamodel-iteration-2`
**Created**: 2026-10-09
**Status**: Implemented
**Input**: "After review of the first iteration: align section kinds with the template method pattern (final / abstract / default) and let refinements seal a section; split skills into atomic and composite; allow inout parameters; support the optional Agent Skills fields; give workflow nodes names. Regenerate everything."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Template method vocabulary and sealing (Priority: P1)

**Acceptance Scenarios**:

1. Section kinds are renamed `fixed` → `final`, `hook` → `default`.
2. **Given** a section refined by a parent, **Then** it is `default` for further
   descendants (`test_refined_sections_become_default`).
3. **Given** a refinement with `final: true`, **Then** descendants may not refine
   that section again (`test_sealed_sections_admit_no_refinement`).
4. S2 and S3 use the *effective* (derived) kind, not the declared one.

### User Story 2 - Atomic and composite skills (Priority: P1)

1. `Skill` becomes abstract; `AtomicSkill` holds sections and refinements;
   `CompositeSkill` holds the graph (`test_composite_skills_have_no_sections`).
2. A skill specializes only skills of its own kind, checked as WF
   (`test_skills_specialize_skills_of_their_kind`).

### User Story 3 - Inout parameters (Priority: P2)

An `inout` parameter is both an input and an output (C2, C3) and is generated as
`deft-updates` (`test_inout_parameters_are_inputs_and_outputs`).

### User Story 4 - Optional specification fields (Priority: P2)

`license`, `compatibility` and `allowed-tools` are inherited and generated; the library
declares a default licence (`test_optional_fields_are_inherited`).

### User Story 5 - Named nodes (Priority: P3)

Workflow nodes have `name` instead of `id`, like every other element.

## Requirements *(mandatory)*

- **FR-001**: Two new mutation operators: `refine-sealed-section`, `cross-kind-parent`
  (`refine-fixed-section` renamed `refine-final-section`); 21 in total.
- **FR-002**: Ecore, OCL, PlantUML, guides, site and `skills/` updated in the same change
  (Constitution III).
- **FR-003**: C5 round 3 recorded; two conditions improved in the models.

## Success Criteria *(mandatory)*

- **SC-001**: 311 mutants, all killed under the intended constraint, 252 only under it.
- **SC-002**: 4 of 16 configurations accepted per workflow; all rejections are C2.
- **SC-003**: 0 violations; 15/15 generated skills valid.
