# Tasks: Metamodel core

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md)

## Phase 1: Setup

- [X] T001 Create package skeleton `deft/__init__.py`, `deft/__main__.py`
- [X] T002 Create `pyproject.toml` (setuptools, PyYAML, optional `test` extras, `deft` script)
- [X] T003 [P] Add GPL-3.0 `LICENSE` and `.gitignore`

## Phase 2: Foundational

- [X] T004 Enumerations `SectionKind`, `RefinementKind`, `Direction`, `ResourceKind`, `OriginMode`, `ControlKind`, `ControlEdgeKind` in `deft/model.py`
- [X] T005 Specialization dataclasses `Property`, `ArtifactType`, `Section`, `Refinement`, `Parameter`, `Resource`, `Origin`, `Skill` in `deft/model.py`
- [X] T006 Composition dataclasses `SkillNode`, `ControlNode`, `Port`, `DataEdge`, `ControlEdge`, `CompositeSkill` in `deft/model.py`

## Phase 3: User Story 1 - Skill families (P1)

- [X] T007 [US1] `Library` with cycle-safe `_chain`, `skill_ancestors`, `conforms_skill` in `deft/model.py`
- [X] T008 [US1] `effective_param`, `effective_params`, `effective_conditions` in `deft/model.py`
- [X] T009 [US1] Loader for skill files: `_parse_skill_common`, `_parse_body`, `_content` in `deft/loader.py`
- [X] T010 [US1] `ModelError` with file and key in `deft/loader.py`

## Phase 4: User Story 2 - Artifact types (P1)

- [X] T011 [P] [US2] `_parse_type`, multiplicity parsing `_mult`, `_upper` in `deft/loader.py`
- [X] T012 [P] [US2] `type_ancestors`, `conforms_type`, `effective_property(ies)` in `deft/model.py`

## Phase 5: User Story 3 - Workflows (P2)

- [X] T013 [US3] `_parse_port` (`node.param`, `self.param`) and `_parse_composite` in `deft/loader.py`
- [X] T014 [US3] `library_from_dict` and `load_library(root)` reading `library.yaml`, `types/`, `skills/`, `workflows/`

## Phase 6: Polish

- [X] T015 [P] `metamodel/deft.ecore` mirroring T004–T006
- [X] T016 [P] PlantUML diagrams `metamodel/deft-specialization.puml`, `metamodel/deft-composition.puml`
- [X] T017 Toy library fixture and `test_valid_toy_library` in `tests/test_constraints.py`
