# Tasks: Formative evaluation (E1–E3)

## Phase 1: Setup

- [X] T001 `experiments/common.py` (`save`, `read`, frontmatter and section splitting, `nonblank`, `tokens`)
- [X] T002 `experiments/run_all.py` and `results/summary.md` writer

## Phase 2: E1 Expressiveness

- [X] T003 [P] [US1] `e1_expressiveness/survey.py` and `mapping.yaml` (14 conventions)
- [X] T004 [P] [US1] `e1_expressiveness/refactor_speckit.py` writing `speckit-model/`; exact round trip

## Phase 3: E2 Checkability

- [X] T005 [US2] `e2_checkability/mutate.py` with 19 operators (iteration 1)
- [X] T006 [US2] `e2_checkability/configurations.py` (16 configurations per workflow)

## Phase 4: E3 Generation

- [X] T007 [US3] `e3_generation/measure.py` (sizes, repeated lines, `skills-ref`)

## Phase 5: Polish

- [X] T008 Token counts with tiktoken `o200k_base` next to lines
- [X] T009 `experiments/README.md` with the operator table and limitations
- [X] T010 CI step `python experiments/run_all.py`
