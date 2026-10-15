# Command line

Install with `pip install -e .` from the repository root; this provides the `deft`
command (or run `python -m deft`).

| Command | Effect |
|---|---|
| `deft check LIB [--json]` | Run the well-formedness checks, S1–S4 and C1–C4. Exit code 1 if there are violations. |
| `deft resolve LIB SKILL` | Print the resolved `SKILL.md` of one skill or workflow, without writing files. |
| `deft generate LIB --out DIR [--no-provenance] [--force]` | Write one folder per concrete skill and executable workflow. Refuses to run on a library with violations unless `--force`. |
| `deft obligations LIB [--workflow W]` | List the C5 contract obligations of the workflows for review. |
| `deft diagram LIB [--workflow W]` | Print a PlantUML diagram of the skill and type hierarchies, or of one workflow. |

`LIB` is a library directory (see [Writing models](modelling-guide.md)), for instance
`models`.

## Typical session

```bash
deft check models
deft resolve models volere | less
deft generate models --out skills
deft obligations models --workflow deliver-feature
```
