# Implementation Plan: Agent run of the example

**Branch**: `006-agent-run` | **Spec**: [spec.md](spec.md)

## Summary

A small existing service and a feature request, a script that prepares a run with the
generated skills, a script that checks what the run produced, and the artifacts of one
recorded run.

## Technical Context

**Example system**: FastAPI, SQLite, pytest (`examples/account-service/requirements.txt`)
**Agent**: Claude Code, run in a separate repository created by `prepare.py`
**Checker**: Python standard library plus `git` and the run's own virtual environment

## Constitution Check

- I. Models in, standard skills out: the agent receives only generated `SKILL.md` folders. PASS
- V. Reproducible evidence: the run itself is not reproducible (agent output varies);
  its artifacts are kept in `recorded-run/` and the checker is reproducible. PASS with note

## Project Structure

```text
examples/account-service/
├── app/                 # existing system
├── tests/test_auth.py   # existing tests
├── FEATURE-REQUEST.md   # the prompt
├── prepare.py           # copy, generate skills, first commit
├── check_run.py         # artifacts, traceability, branch, commits, verdict
└── recorded-run/        # artifacts of one run + README mapping them to steps
```

## Design decisions

1. **Run outside the repository.** `prepare.py` copies the system so the run's commits
   do not mix with DEFT's history.
2. **Check against the workflow, not against a gold output.** `check_run.py` checks what
   the skills prescribe (files, requirement ids cited by tests, branch, passing suite).
3. **Requirement ids as the trace.** Ids `US-`, `FR-`, `QR-` are matched in test files.
4. **Count only new commits.** Commits are counted on top of the prepared baseline.
