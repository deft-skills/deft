# Example: deliver a feature with DEFT skills

This example runs the `deliver-feature` workflow of the DEFT example library
with a real coding agent, on a small existing system.

**The system.** An account service (FastAPI, SQLite, pytest) where users can
register and log in: [app/main.py](app/main.py), with three tests in
[tests/test_auth.py](tests/test_auth.py).

**The feature request** ([FEATURE-REQUEST.md](FEATURE-REQUEST.md)). Users who
forgot their password can reset it through a link sent by e-mail; the link
expires after 15 minutes and can be used once; the reset request responds in
under 500 ms at the 95th percentile with 200 concurrent users.

**What the agent should do**, following the generated workflow skill:

1. specify the functional requirements as user stories and the quality requirement
   as a Volere snow card (`specs/<feature>/requirements.md`);
2. plan test-first tasks (`specs/<feature>/plan.md`);
3. implement them on a feature branch, test-driven, keeping a ledger (`progress.md`);
4. write acceptance tests (Gherkin, pytest-bdd) and a performance test (Locust);
5. debug and repair, at most three times, if a test fails.

## Steps

### 1. Prepare a run folder

From the root of the DEFT repository:

```bash
python examples/account-service/prepare.py --dest ../deft-run
```

This checks the DEFT library, copies the system to `../deft-run`, generates the
15 skills into `../deft-run/.claude/skills/`, and makes a first commit. For an
agent that reads skills from another folder, pass `--skills-dir`, for instance
`--skills-dir .agents/skills`; see the documentation of your agent and the list
of compatible clients at <https://agentskills.io/clients>.

### 2. Set up the system

```bash
cd ../deft-run
python -m venv .venv
.venv/bin/pip install -r requirements.txt          # Windows: .venv\Scripts\pip
.venv/bin/python -m pytest                         # 3 passed
```

### 3. Run the agent

Start your coding agent in `../deft-run` and give it the content of
`FEATURE-REQUEST.md` as the prompt. It starts with: *Use the skill
`deliver-feature` for this feature request.* With Claude Code:

```bash
claude                                             # then paste FEATURE-REQUEST.md
```

Answer the clarification questions the requirements skills may ask (at most
three). Let the agent run to the end; it decides small issues itself and records
them as rulings in its ledger.

### 4. Check the result

From the DEFT repository:

```bash
python examples/account-service/check_run.py ../deft-run --json ../deft-run-report.json
```

The report lists the artifacts the workflow prescribes, the requirement ids and
the tests that cite them (traceability), the branch and the number of commits,
and the verdict of the test suite. Compare it with what the workflow promises in
`../deft-run/.claude/skills/deliver-feature/SKILL.md` ("Done when").

## A recorded run

[recorded-run/](recorded-run/) records one run of this example with Claude Code,
without any human input after the prompt. The agent loaded the nine skills in the
order of the workflow, produced every artifact the workflow prescribes, traced all
seven requirements to tests, and used one of its three repairs after the first load
test failed. Its README lists the artifacts and the workflow step that produced each
one; `session-summary.json` lists the skills with their timestamps, and
`diff-stat.txt` the files the agent changed.

## What to look at

- Did the agent load the skills in the order of the workflow, and the bound ones
  (`user-stories`, `volere`, `execute-plan-inline`, `acceptance-gherkin`)?
- Does every requirement id appear in at least one test?
- Did a failure trigger `systematic-debugging` and a bounded repair?
- Try the ISO/IEC 25010 variant: prompt with `deliver-feature-iso` instead.
