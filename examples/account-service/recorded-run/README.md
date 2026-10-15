# Recorded run

Artifacts of one run of `deliver-feature` on this example with Claude Code
(`claude-opus-5`), copied from the run's repository so that they travel with DEFT.
The prompt was [FEATURE-REQUEST.md](../FEATURE-REQUEST.md); there was no human input
after it.

| File | What it is | Workflow step |
|---|---|---|
| [session-summary.json](session-summary.json) | Skills loaded with their times, tool calls, duration, output tokens (from the agent's session log) | all |
| [requirements.md](requirements.md) | User stories US-1..4 with Given/When/Then criteria, Volere requirements QR-1..3 with fit criteria, assumptions, validation | specify (`user-stories`, `volere`) |
| [plan.md](plan.md) | Tasks T1..T8 | plan (`plan-feature`) |
| [progress.md](progress.md) | Ledger: completed tasks, rulings, final review, repair loop | implement (`execute-plan-inline`, invoking `test-driven-development`) |
| [acceptance-report.md](acceptance-report.md) | Acceptance verdict | acceptance (`acceptance-gherkin`) |
| [performance-report.md](performance-report.md) | Load-test verdicts, the failing first run and the passing final run | performance (`performance-tests`) |
| [diagnosis.md](diagnosis.md) | Root causes of the failing load run | debug (`systematic-debugging`), then repair 1 of 3 |
| [check-report.json](check-report.json) | Output of `check_run.py`: artifacts, traceability from requirement ids to tests, branch, commits, test verdict | done-when |
| [diff-stat.txt](diff-stat.txt) | Files changed by the agent | |
