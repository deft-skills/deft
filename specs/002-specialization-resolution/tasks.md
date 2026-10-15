# Tasks: Specialization — resolution and S1–S4

## Phase 1: Foundational

- [X] T001 `Violation` dataclass and `__str__` in `deft/check.py`
- [X] T002 `check_well_formed`: unresolved parent, type, role, binding, node, parameter in `deft/check.py`
- [X] T003 [P] `strip_frontmatter`, `extract_section`, `demote` for `source:` content in `deft/loader.py`

## Phase 2: User Story 1 - Resolution (P1)

- [X] T004 [US1] `Contribution`, `ResolvedSection`, `ResolvedSkill` in `deft/resolve.py`
- [X] T005 [US1] `resolve(lib, name)` applying implements/overrides/extends root-first
- [X] T006 [US1] `effective_metadata`, `substitute` for `{{name}}` and `{{meta.*}}`
- [X] T007 [US1] `provenance_trail` rendering
- [X] T008 [US1] `deft resolve` in `deft/cli.py`
- [X] T009 [P] [US1] `test_resolution_and_provenance`, `test_placeholders`

## Phase 3: User Story 2 - Checks (P1)

- [X] T010 [US2] `check_s1` with `_has_cycle`; at most one parent
- [X] T011 [US2] `check_s2` concrete skills implement every inherited abstract section
- [X] T012 [US2] `check_s3` refinement target and kind vs. inherited kind; no redeclaration
- [X] T013 [US2] `check_s4` parameter direction and type narrowing; property multiplicity `_within`
- [X] T014 [US2] WF: resource folder matches kind; `imported` origin iff `source`
- [X] T015 [US2] `check_library`; `deft check` with `--json` and exit codes 0, 1 (violations), 2 (model error)
- [X] T016 [P] [US2] Tests `test_s1_*`, `test_s2_*`, `test_s3_*`, `test_s4_*`, `test_wf_*`

## Phase 4: Polish

- [X] T017 [P] OCL invariants WF, S1–S4 in `metamodel/deft.ocl`
- [X] T018 [P] Constraint table and "Why input narrowing is allowed" in `guides/constraints.md`
