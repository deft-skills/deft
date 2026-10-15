# Tasks: Skill generation

## Phase 1: Setup

- [X] T001 Pin upstream skills by commit under `upstream/` with `UPSTREAM.yaml` and licences
- [X] T002 [P] `NOTICE` listing third-party material

## Phase 2: User Story 1 - Standard skills (P1)

- [X] T003 [US1] `_frontmatter` with `deft-version`, `deft-lineage`, `deft-inputs`, `deft-outputs`, `deft-origin` in `deft/generate.py`
- [X] T004 [US1] `_io_section`, `_artifact_lines`, `_conditions` in `deft/generate.py`
- [X] T005 [US1] `render_skill(lib, name, provenance)` in `deft/generate.py`
- [X] T006 [US1] `generate(lib, out_dir)` skipping abstract skills and non-executable workflows
- [X] T007 [US1] `deft generate --out --force --no-provenance` in `deft/cli.py`
- [X] T008 [P] [US1] `test_abstract_sections_never_reach_agents`
- [X] T009 [P] [US1] `test_generated_skills_pass_reference_validator` (requires `skills-ref`, Python 3.11)

## Phase 3: User Story 2 - Provenance and licences (P1)

- [X] T010 [US2] `upstream_licenses`, `_origin_line`; copy `LICENSE-*.txt` into derived skills
- [X] T011 [US2] Copy ancestor resources, nearest declaration wins
- [X] T012 [P] [US2] `test_upstream_licences_travel_with_adapted_skills`

## Phase 4: User Story 3 - Workflows (P2)

- [X] T013 [US3] `topological_steps` and `render_workflow` with `deft-requires`
- [X] T014 [US3] `mermaid` into `references/workflow.mmd`
- [X] T015 [P] [US3] `test_workflow_order_respects_dependencies`

## Phase 5: Polish

- [X] T016 CI job: pytest, `deft check`, regenerate `skills/` and fail on diff (Python 3.11 and 3.13)
- [X] T017 [P] `guides/generation.md`
