# Tasks: Composition — C1–C4 and C5 obligations

## Phase 1: Foundational

- [X] T001 `_port_param` resolving `node.param` on the effective skill, and `self` ports, in `deft/check.py`
- [X] T002 `_check_edge_types` (type conformance, many-to-single) in `deft/check.py`

## Phase 2: User Story 1 - Checks (P1)

- [X] T003 [US1] `check_c1` binding concrete and within the role's family
- [X] T004 [US1] `check_c2` over data edges and repair payloads
- [X] T005 [US1] `check_c3` mandatory inputs fed (or supplied by caller); workflow outputs produced
- [X] T006 [US1] `check_c4` acyclic without repair; bound ≥ 1; invoked node has one caller
- [X] T007 [US1] `check_composite`, `is_executable`; call from `check_library`
- [X] T008 [P] [US1] Tests `test_c1_*`, `test_c2_*`, `test_c3_*`, `test_c4_*`, `test_running_example_seeded_faults`

## Phase 3: User Story 2 - Obligations (P2)

- [X] T009 [US2] `Obligation` dataclass and `obligations(lib, comp)` in `deft/check.py`
- [X] T010 [US2] `deft obligations [--workflow]` in `deft/cli.py`
- [X] T011 [US2] "C5 in practice" section in `guides/constraints.md`

## Phase 4: Polish

- [X] T012 [P] OCL invariants C1–C4 in `metamodel/deft.ocl`
- [X] T013 [P] `deft diagram` (PlantUML of a library or workflow) in `deft/diagram.py`
