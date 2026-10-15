# Feature Specification: Specialization — resolution and S1–S4

**Feature Branch**: `002-specialization-resolution`
**Created**: 2026-10-07
**Status**: Implemented
**Input**: "A concrete skill must resolve to the text an agent receives: take the root's sections and apply every descendant's refinements in order, recording who changed what. Reject hierarchies that cannot resolve soundly, following the template method pattern."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what an agent receives (Priority: P1)

A skill author runs `deft resolve models volere` and reads the full instructions of
`volere`, with every section and the skill that last wrote it.

**Independent Test**: `test_resolution_and_provenance`.

**Acceptance Scenarios**:

1. **Given** `specify-requirements` (abstract `structure`, hook `validate`) and
   `volere` which implements `structure` and extends `validate`, **When** I resolve
   `volere`, **Then** `structure` holds Volere's text and `validate` holds the root's
   text followed by Volere's addition.
2. **Given** a resolved section, **When** I print its provenance, **Then** I see the
   declaring skill followed by each refining skill and its refinement kind.
3. **Given** a section with `{{name}}` or `{{meta.title}}`, **When** it is resolved,
   **Then** the placeholder is replaced by the skill's name or inherited metadata
   (`test_placeholders`).

### User Story 2 - Reject unsound hierarchies (Priority: P1)

The author runs `deft check models` and gets one violation per broken rule, with a
code and a message that names the skill and section.

**Independent Test**: one test per rule (`test_s1_*` to `test_s4_*`).

**Acceptance Scenarios**:

1. **Given** a cycle in the skill or type hierarchy, **Then** S1.
2. **Given** a concrete skill that leaves an inherited abstract section empty, **Then** S2.
3. **Given** an `overrides` on a fixed section, an `implements` on a hook, or a
   redeclared inherited section, **Then** S3.
4. **Given** a redeclared parameter that widens its type or flips its direction, or a
   subtype property that widens its multiplicity, **Then** S4.
5. **Given** a dangling reference, a resource outside its kind's folder, or an
   `imported` origin without a `source`, **Then** WF.

### Edge Cases

- A descendant may **narrow** an input type. Behavioural subtyping forbids this; skill
  families need it (acceptance tests take only user stories). S4 accepts it and the
  check moves to the binding site (feature 003, C2).
- Narrowing a property multiplicity is allowed (`test_s4_property_narrowing_is_allowed`).
- Resolution must still run on an invalid library (refinements on missing targets are skipped, reported by S3).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `resolve(lib, name)` MUST return the sections in declaration order from
  the root, with content after all refinements on the chain root → skill.
- **FR-002**: `implements` and `overrides` MUST replace content; `extends` MUST append.
- **FR-003**: Each resolved section MUST record its contributions (skill, action).
- **FR-004**: Placeholders `{{name}}` and `{{meta.<key>}}` MUST be substituted after resolution.
- **FR-005**: Sections and refinements MAY read content from a pinned upstream file
  (`source`, optionally one heading of it); the text is demoted to fit the hierarchy.
- **FR-006**: The checker MUST implement WF, S1, S2, S3, S4 and return `Violation(code, element, message)`.
- **FR-007**: Every rule MUST also exist as an OCL invariant in `metamodel/deft.ocl`
  and as a row in `guides/constraints.md` (Constitution III).
- **FR-008**: `deft resolve <models> <skill>` MUST print the resolved `SKILL.md`.

## Success Criteria *(mandatory)*

- **SC-001**: The example library has 0 violations.
- **SC-002**: Each rule has at least one test that triggers it and only it.
- **SC-003**: Resolution of every concrete skill in the example contains no abstract section.
