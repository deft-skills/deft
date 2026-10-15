# Tasks: C5 review by people and LLM judges

- [X] T001 [US1] `c5_contracts/obligations.py` writing `results/c5_obligations.{json,md}`
- [X] T002 [US1] `review.yaml` round 1 (5/8 entailed, 3 gaps)
- [X] T003 [US1] Fix the models: execute-plan postconditions (full suite, branch); workflow precondition (environment)
- [X] T004 [US1] `review.yaml` round 2 (8/8 entailed)
- [X] T005 [US2] `items.py` rebuilding the first models, 16 shuffled items with reference verdicts
- [X] T006 [US2] `.env.example`; `judge.py` with Anthropic and OpenAI; answer cache
- [X] T007 [US2] Add Google judge after quota issue
- [X] T008 [US2] `review_text.py`: workflow overview, definitions, grouped guarantees; counterbalanced rounds; item fingerprint
- [X] T009 [US2] `make_sheet.py` building `human/c5-review-sheet.html`; `human/README.md`
- [X] T010 [US2] `analyse.py` (accuracy, gaps, false alarms, kappa) → `results/c5_agreement.{json,md}`
- [X] T011 [US3] Collect the second reviewer's answers (`human/answers/c5-answers-R1.json`)
- [X] T012 [US3] `review.yaml` round 3; two conditions improved in the models
