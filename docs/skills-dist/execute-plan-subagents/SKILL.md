---
name: execute-plan-subagents
description: Use when the plan must be executed by a fresh implementer subagent per task, each followed by a task review.
license: GPL-3.0-only (includes third-party material; see LICENSE-*.txt)
metadata:
  deft-version: 0.1.0
  deft-lineage: execute-plan > execute-plan-subagents
  deft-inputs: 'plan: ImplementationPlan [1]; diagnosis: Diagnosis [0..1]'
  deft-outputs: 'code: SourceCode [1]'
  deft-origin: obra/superpowers@8ca22db skills/executing-plans/SKILL.md (MIT, adapted); obra/superpowers@8ca22db skills/subagent-driven-development/SKILL.md (MIT, adapted)
---

# Execute the plan with subagents

## Inputs and outputs

- Input `plan`: ImplementationPlan (one)
  Ordered, test-first tasks that implement a set of requirements.
  - `fileStructure` (required)
  - `tasks` (one or more): each task names files, interfaces, tests and the requirement ids it covers
  - `reviewFocus` (any number)
- Input `diagnosis`: Diagnosis (optional). Present when the workflow returns after a failure.
  Root cause of a failure and the change that fixes it.
  - `rootCause` (required)
  - `evidence` (one or more)
  - `fix` (required)
- Output `code`: SourceCode (one)
  The changed code base, as a branch or a set of commits.
  - `branch` (required)
  - `commits` (one or more)

## Before you start

- The plan has at least one task and every task names its test.

## Principles
<!-- deft: final section 'principles'; declared by execute-plan -->

The requirements are the binding authority and the plan is their argument.
Execute the plan exactly and without pausing between tasks. Decide
conflicts, ambiguities and plan defects yourself and record each decision
in the ledger as `Ruling: <decision> - <why> - <cost if wrong>`.

Stop and ask only for: an irreversible or destructive operation; a
security-sensitive action; a side effect outside the workspace (merge,
push to a shared branch, publish); or a plan so broken that every path
forward is a guess.

## Set up the workspace
<!-- deft: final section 'setup'; declared by execute-plan -->

Work on a dedicated branch or worktree, never on the main branch without
consent. Create a ledger file `progress.md` in the workspace whose first
line names the plan. If the ledger exists, read it and resume after the
last completed task. Read the plan once and create one todo per task.
If you received a diagnosis, read it first: the repair concerns only the
tasks it names.

## Run the task loop
<!-- deft: default section 'loop'; declared abstract by execute-plan, implemented by execute-plan-subagents -->

For each task, in order (never two implementers in parallel):

1. Record BASE. Extract the task to a brief file and dispatch a fresh
   implementer with: where the task fits, the brief path ("read this
   first; use its values verbatim"), interfaces decided by earlier tasks,
   your resolution of ambiguities, and a report-file path.
2. Handle the report: DONE goes to review; DONE_WITH_CONCERNS is read
   before review; NEEDS_CONTEXT is answered and re-dispatched; BLOCKED is
   fixed by more context, a more capable model, a smaller task, or a
   ruling on the plan.
3. Dispatch a task reviewer with the brief, the report and the diff from
   BASE. Require both verdicts: compliance with the requirements and code
   quality.
4. Fix loop: send open critical or important findings back to the
   implementer, at most five rounds, each followed by a scoped re-review.
   At the limit, rule on each open finding and record it.
5. Apply the completion contract.

## Completion contract
<!-- deft: final section 'contract'; declared by execute-plan -->

A task is complete only when, with evidence from this session:

- every test the task names exists, ran, and you read its output;
- the final run of the task's tests passed;
- every expected output in the plan was compared with the real output;
- every deviation has a ruling in the ledger.

Then append `Task <N>: complete (commits <base>..<head>, tests: <command> -> <result>)`
to the ledger.

## Final review
<!-- deft: default section 'final-review'; declared by execute-plan, extended by execute-plan-subagents -->

When all tasks are complete, review the whole branch against the
requirements and the plan's review focus. Fix critical and important
findings in one pass, each with a test that failed first. Record minor
findings in the ledger as deferred. Report the rulings you made and the
deferred findings.

Dispatch the final reviewer on the most capable available model, with the
plan, the requirements, the review focus and the ledger's rulings.

## Done when

- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.
