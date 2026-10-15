# Implementation Plan: C5 review by people and LLM judges

**Branch**: `008-c5-review` | **Spec**: [spec.md](spec.md)

## Summary

Record the reference review of the C5 obligations, rebuild the obligations from before
and after the fixes as blind review items, collect answers from a second person and
three LLM judges with the same instructions, and compute agreement.

## Technical Context

**Language/Version**: Python 3.11+
**Dependencies**: none; the judges call the Anthropic, OpenAI and Google APIs with
`urllib` (providers without a key are skipped)
**Secrets**: `.env` (git-ignored); `.env.example` documents the keys and models
**Outputs**: `results/c5_items.json`, `c5_judges.json`, `c5_judge_cache.json`, `c5_agreement.{json,md}`

## Constitution Check

- II. Check before execution: C5 stays a human review; judges are studied, not trusted. PASS
- V. Reproducible evidence: judge answers are cached, so a rerun needs no keys. PASS

## Project Structure

```text
experiments/c5_contracts/
├── obligations.py    # obligations for review
├── review.yaml       # reference review, rounds 1–3
├── items.py          # 16 items, shuffled, with reference verdicts
├── review_text.py    # shared instructions: overview, definitions, grouped guarantees
├── judge.py          # LLM judges
├── make_sheet.py     # self-contained HTML sheet for people
├── analyse.py        # accuracy, gaps, false alarms, Cohen's kappa
└── human/            # README, sheet, answers/
```

## Design decisions

1. **Same text for people and judges** (`review_text.py`), so differences come from the
   reviewer, not the prompt.
2. **Freeze the reviewed items.** Later model fixes do not change the items, so recorded
   answers stay valid (`items.py`, `REVIEWED`).
3. **Counterbalanced rounds.** Each step's before and after versions go to different
   rounds, with 4 items of each version per round and the failing obligations split
   across both, so a reviewer never compares the two versions side by side.
4. **Item fingerprint.** A hash of the items is stored with the answers, so answers are
   never matched to a different item set.
5. **An HTML sheet with no server**, so a reviewer only needs a browser and returns a JSON file.
