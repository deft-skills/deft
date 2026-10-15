# CLI contract: `deft check`, `deft resolve`

## `deft check <models> [--json]`

- Loads the library at `<models>`; a `ModelError` prints `model error: …` to stderr and exits 2.
- Prints one line per violation, `[<CODE>] <element>: <message>`, then the summary
  `N types, M skills: K violation(s)`.
- With `--json`, prints the violations as a JSON list of `{code, element, message}`.
- Exit code 0 when K = 0, 1 otherwise.

Example (example library): `14 types, 21 skills: 0 violation(s)`.

## `deft resolve <models> <skill>`

- Prints the `SKILL.md` an agent would receive for `<skill>`: frontmatter, resolved
  sections with provenance comments. A composite skill is rendered as a workflow.
- An unknown skill prints `unknown skill '<name>'` to stderr and exits 2.
- Abstract skills are not refused; their abstract sections are rendered as empty.
