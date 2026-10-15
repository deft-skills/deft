# Feature Specification: Skill generation

**Feature Branch**: `004-skill-generation`
**Created**: 2026-10-07
**Status**: Implemented
**Input**: "Agents must not need DEFT. Generate one standard SKILL.md folder per concrete skill and per executable workflow, with lineage, signature, origin and provenance, and with the licences of reused material. The output must pass the specification's validator."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a library of standard skills (Priority: P1)

A skill author runs `deft generate models --out skills` and gets one folder per
concrete skill that any Agent Skills–compatible agent can load.

**Independent Test**: `test_generated_skills_pass_reference_validator` (runs `skills-ref`).

**Acceptance Scenarios**:

1. **Given** the example library, **When** I generate, **Then** 15 folders are written
   (21 skills minus 6 abstract) and each passes `skills-ref validate`.
2. **Given** an ill-formed library, **When** I generate, **Then** generation is
   refused with the violations, unless `--force` is given.
3. **Given** any generated skill, **Then** no abstract section reaches it
   (`test_abstract_sections_never_reach_agents`).

### User Story 2 - Keep provenance and licences (Priority: P1)

A maintainer can see where each instruction came from and which licences apply.

**Independent Test**: `test_upstream_licences_travel_with_adapted_skills`.

**Acceptance Scenarios**:

1. **Given** `volere`, which adapts Spec Kit, **Then** its folder contains
   `LICENSE-spec-kit.txt` and its frontmatter licence notes third-party material.
2. **Given** provenance enabled (default), **Then** each section carries an HTML
   comment naming the declaring and refining skills; `--no-provenance` removes them.
3. **Given** resources declared on an ancestor, **Then** they are copied into the
   descendant's folder; the nearest declaration wins.

### User Story 3 - Generate an executable workflow (Priority: P2)

A process owner generates `deliver-feature` as a skill that tells the agent which
skills to load, in which order, and which artifacts to pass.

**Independent Test**: `test_workflow_order_respects_dependencies`.

**Acceptance Scenarios**:

1. **Given** a workflow whose roles are all bound to concrete skills, **Then** it is
   generated with `deft-requires` listing the skills it calls and with steps in
   topological order.
2. **Given** a workflow with an unbound abstract role, **Then** it is not generated.
3. **Given** a generated workflow, **Then** `references/workflow.mmd` holds a Mermaid
   diagram of the graph.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The frontmatter MUST contain `name`, `description`, `license` and `metadata`
  with `deft-version`, `deft-lineage`, `deft-inputs`, `deft-outputs` and, when applicable,
  `deft-origin` and `deft-requires`.
- **FR-002**: The body MUST contain the inputs and outputs with the fields of their
  artifact types, the pre- and postconditions, and the resolved sections.
- **FR-003**: Third-party skills MUST be pinned by commit under `upstream/` and listed
  in `upstream/UPSTREAM.yaml` and `NOTICE`.
- **FR-004**: `deft generate <models> --out DIR [--force] [--no-provenance]`.
- **FR-005**: CI MUST fail if `skills/` differs from a fresh generation.

## Success Criteria *(mandatory)*

- **SC-001**: 15/15 generated skills pass `skills-ref`.
- **SC-002**: Generation is deterministic (CI diff is empty on a clean tree).
