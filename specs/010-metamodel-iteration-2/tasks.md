# Tasks: Metamodel iteration after review

## Phase 1: Metamodel

- [X] T001 [US1] Rename `SectionKind` values to `final`, `abstract`, `default` in `deft/model.py`
- [X] T002 [US1] `Refinement.final` (sealing); derived kinds in `deft/resolve.py`
- [X] T003 [US2] `AtomicSkill(Skill)` with sections and refinements; `CompositeSkill(Skill)`
- [X] T004 [US3] `Direction.INOUT`, `is_input`, `is_output`
- [X] T005 [US4] `license`, `compatibility`, `allowed_tools` on `Skill`; `Library.license`
- [X] T006 [US5] `SkillNode.name`, `ControlNode.name`; ports by node name

## Phase 2: Checks and generation

- [X] T007 [US1] S2, S3 on effective kinds
- [X] T008 [US2] WF: same-kind parent; composite skills have no sections
- [X] T009 [US3] C2, C3 treat `inout` as input and output; `deft-updates` in frontmatter
- [X] T010 [US4] `effective_attribute`; generate `license`, `compatibility`, `allowed-tools`
- [X] T011 [P] Tests for each user story in `tests/test_constraints.py`, `tests/test_generate.py`

## Phase 3: Models and evidence

- [X] T012 Update all models (`fixed`/`hook` → `final`/`default`, node names)
- [X] T013 Mutation operators `refine-sealed-section`, `cross-kind-parent`; rerun → 311 mutants
- [X] T014 C5 round 3 in `review.yaml`; two conditions improved
- [X] T015 Regenerate `skills/`, `results/`, `docs/`

## Phase 4: Forms of the metamodel

- [X] T016 [P] `metamodel/deft.ecore`, `metamodel/deft.ocl`
- [X] T017 [P] PlantUML diagrams and PNG/SVG renders
- [X] T018 [P] Guides `metamodel.md` (resolution figure), `modelling-guide.md`, `constraints.md`, `generation.md`
