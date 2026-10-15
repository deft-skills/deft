# Feature Specification: Composition — C1–C4 and C5 obligations

**Feature Branch**: `003-composition-checks`
**Created**: 2026-10-07
**Status**: Implemented
**Input**: "Workflows bind abstract roles to concrete skills. Check the bindings, the data flow and the control flow before any agent runs. Pre- and postconditions are prose: list what must be entailed, for people to review."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Catch a wrong binding before execution (Priority: P1)

A process owner binds the `functional` node of `deliver-feature` to `ears` instead of
`user-stories`. The acceptance-test skill only accepts user stories. `deft check`
reports a type error at the edge, although `ears` and the acceptance skill are each
valid in their own hierarchy.

**Why this priority**: This is the cross-dimension error that checking each hierarchy
alone misses; it motivates checking specialization and composition together.

**Independent Test**: `test_c2_cross_dimension_type_error`.

**Acceptance Scenarios**:

1. **Given** a node bound to an abstract skill or to a skill outside its role's family,
   **Then** C1.
2. **Given** a data edge whose source type (on the *bound* skills) does not conform to
   the target type, or a many-valued source feeding a single-valued input, **Then** C2.
3. **Given** a template with unbound roles, **Then** C2 is checked on the roles
   (`test_c2_unbound_template_is_checked_on_roles`).
4. **Given** a mandatory input with no incoming data edge (and not supplied by an
   invoking caller), or a mandatory workflow output never produced, **Then** C3.
5. **Given** a cycle without repair edges, a repair edge with bound < 1, or an invoked
   node with two callers or another incoming control edge, **Then** C4.

### User Story 2 - Review the contracts that cannot be decided (Priority: P2)

A reviewer runs `deft obligations models --workflow deliver-feature` and, for each
node, reads the guarantees of its predecessors and the preconditions they must entail.

**Independent Test**: the command lists 8 obligations for `deliver-feature`.

**Acceptance Scenarios**:

1. **Given** node `implement` reached by `plan` (data) and by `debug` (repair),
   **When** obligations are listed, **Then** the guarantees include the
   postconditions of both and the precondition of `implement` appears under
   "must entail".
2. **Given** a node reached through a guarded edge, **Then** the guard is listed as a guarantee.

### Edge Cases

- Repair payloads (`carries`) are data edges and are type-checked by C2.
- `self` ports: inputs of the workflow are sources, outputs are targets.
- A workflow is *executable* (generated) only when every role is bound to a concrete skill or is concrete itself.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The checker MUST implement C1–C4 on every composite skill.
- **FR-002**: C2 MUST evaluate types on the effective skill of each node (`bind or role`).
- **FR-003**: `obligations(lib, comp)` MUST return, per node with preconditions, the
  predecessor postconditions, reaching guards and workflow preconditions, and the
  node's preconditions, plus one obligation for the workflow's own postconditions.
- **FR-004**: The checker MUST NOT decide C5; it only lists obligations.
- **FR-005**: `deft obligations <models> [--workflow NAME]` MUST print the obligations.
- **FR-006**: C1–C4 MUST have OCL invariants and guide rows (Constitution III).

## Success Criteria *(mandatory)*

- **SC-001**: Both example workflows pass C1–C4.
- **SC-002**: Of the 16 binding configurations of each workflow, the checker accepts
  exactly those that are type-safe (measured in feature 007).
- **SC-003**: `deliver-feature` yields 8 obligations.
