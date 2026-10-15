# Feature Specification: Metamodel core

**Feature Branch**: `001-metamodel-core`
**Created**: 2026-10-07
**Status**: Implemented
**Input**: "Agent skills are folders of prose that nobody relates. Give skill libraries a metamodel with two dimensions: specialization (skills and artifact types in hierarchies) and composition (workflows of skills that exchange typed artifacts). Models are YAML; the metamodel must also exist in Ecore so MDE tools can read it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Describe a skill family in a model (Priority: P1)

A skill author writes one YAML file that declares an abstract skill with its shared
procedure and several concrete variants, instead of copying one `SKILL.md` per
variant.

**Why this priority**: Without a model of skills there is nothing to check or generate.

**Independent Test**: Load `models/` with `deft check models` and obtain a library
with all skills and types and no load error.

**Acceptance Scenarios**:

1. **Given** a YAML file with `family: requirements` and a list of skills, **When**
   the loader reads it, **Then** every skill is in the library with its family, parent,
   sections, refinements, parameters, contracts, resources and origin.
2. **Given** a skill that references an unknown parent, **When** the library is
   loaded, **Then** the reference is kept and reported later by the checker (WF),
   not by a loader crash.
3. **Given** a model missing a required key (`name`, `description`), **When** it is
   loaded, **Then** a `ModelError` names the file and the missing key.

### User Story 2 - Describe the artifacts that skills exchange (Priority: P1)

The author declares artifact types (e.g., `Requirement`, `UserStory`) with
properties and multiplicities, organized in their own hierarchy.

**Independent Test**: `Library.conforms_type("UserStory", "Requirement")` is true;
the effective properties of `UserStory` include those inherited from `Requirement`.

**Acceptance Scenarios**:

1. **Given** `UserStory` with parent `FunctionalRequirement` with parent
   `Requirement`, **When** I ask for its ancestors, **Then** I get the chain nearest
   first.
2. **Given** a subtype that redeclares a property, **When** effective properties are
   computed, **Then** the nearest declaration wins.

### User Story 3 - Describe a workflow (Priority: P2)

The author declares a composite skill as a graph of nodes, data edges between ports,
and control edges.

**Independent Test**: Load `models/workflows/deliver-feature.yaml`; the composite has
10 nodes, 15 data edges and 6 control edges.

### Edge Cases

- Upper bound `"*"` must load as many-valued (`MANY = -1`).
- A port written `self.request` refers to the composite's own parameter.
- Cyclic parent chains must not hang the helpers (`_chain` is cycle-safe).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The metamodel MUST provide `Library`, `ArtifactType`, `Property`,
  `Skill`, `Section`, `Refinement`, `Parameter`, `Resource` and `Origin`
  (specialization package).
- **FR-002**: The metamodel MUST provide `CompositeSkill`, `SkillNode`, `ControlNode`,
  `DataEdge`, `ControlEdge` and `Port` (composition package).
- **FR-003**: Sections MUST have one of three kinds: `fixed`, `abstract`, `hook`.
- **FR-004**: Refinements MUST have one of three kinds: `implements`, `overrides`, `extends`.
- **FR-005**: Parameters MUST have a direction (`in`, `out`), a type and a multiplicity.
- **FR-006**: Control nodes MUST be `decision` or `final`; control edges `sequence`,
  `invokes` or `repair` (repair with a bound and an optional carried data edge).
- **FR-007**: Skills MUST carry pre- and postconditions as natural-language lists.
- **FR-008**: An `Origin` MUST record repo, path, commit, licence and mode
  (`adapted` or `imported`).
- **FR-009**: The loader MUST read a library from a folder of YAML files
  (`library.yaml`, `types/`, `skills/`, `workflows/`).
- **FR-010**: The metamodel MUST also be published as Ecore (`metamodel/deft.ecore`)
  with the same classes and enumerations.

### Key Entities

See [data-model.md](data-model.md).

## Success Criteria *(mandatory)*

- **SC-001**: The example library (14 types, 21 skills) loads without error.
- **SC-002**: Every class and enumeration in `deft/model.py` has a counterpart in the Ecore file.
- **SC-003**: The loader adds no dependency beyond PyYAML.
