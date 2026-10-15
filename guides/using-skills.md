# Using generated skills

The skills DEFT generates are ordinary Agent Skills: one folder per skill with a
`SKILL.md` and its bundled files. Any agent that supports the specification can use
them; the DEFT structure stays in the models.

## 1. Generate

```bash
deft check models                      # must report 0 violations
deft generate models --out skills      # one folder per concrete skill and executable workflow
```

Generation refuses to run on a library with violations (use `--force` only to inspect
the output of a broken library).

## 2. Install into your agent

Copy the folders, or generate straight into the folder your agent reads. For a project
with Claude Code:

```bash
deft generate models --out path/to/project/.claude/skills
```

Other agents read skills from other folders (for example `.agents/skills/` in the
project or a folder in your home directory); check the documentation of your agent and
the list of compatible clients at <https://agentskills.io/clients>.

Install a workflow together with every skill it lists in `metadata.deft-requires`;
generating the whole library does that for you.

## 3. Run a workflow

Ask the agent to use the workflow skill by name and give it the inputs listed under
"Inputs and outputs" of its `SKILL.md`, for example:

> Use the skill `deliver-feature` for this feature request: users who forgot their
> password can reset it through a link sent by e-mail...

The workflow skill tells the agent which skill to load at each step, which artifact
each step receives and produces, which skills to invoke inside a step, how to decide
after verification, and how many repair attempts are allowed.

## 4. Check what happened

Compare the result with the workflow's "Done when" list and with the postconditions of
each step. The example in [`examples/account-service`](../examples/account-service/)
provides a system, a feature request, a preparation script and a checker that reports
the produced artifacts, the traceability from requirements to tests, the commits and
the test verdict.

## Updating skills

Change the models, never the generated files: run `deft check` and `deft generate`
again. Imported upstream content (`mode: imported`) is refreshed by updating the pinned
copy under `upstream/` and regenerating; adapted content needs a review of the upstream
change.
