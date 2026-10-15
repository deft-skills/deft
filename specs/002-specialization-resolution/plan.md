# Implementation Plan: Specialization — resolution and S1–S4

**Branch**: `002-specialization-resolution` | **Spec**: [spec.md](spec.md)

## Summary

Add `deft/resolve.py` (resolution with provenance and placeholders), the
specialization checks in `deft/check.py`, their OCL invariants, and the `check` and
`resolve` CLI commands.

## Technical Context

**Language/Version**: Python 3.11+ | **Dependencies**: none new | **Testing**: pytest

## Constitution Check

- II. Check before execution: S1–S4 and WF are decidable and checked. PASS
- III. One rule, three forms: each check gets an OCL invariant, a guide row and a test. PASS
- IV. Reference, do not copy: `source:` reads pinned upstream files. PASS

## Project Structure

```text
deft/
├── resolve.py    # Contribution, ResolvedSection, ResolvedSkill, resolve, substitute
├── check.py      # Violation, check_well_formed, check_s1..s4, check_library
└── cli.py        # deft check | resolve
metamodel/deft.ocl
guides/constraints.md
tests/test_constraints.py
```

## Design decisions

1. **Resolution walks the chain root-first**, applies refinements of each skill, then
   appends the sections it declares. A redeclared section is skipped (reported by S3).
2. **Provenance is data**, not comments: `ResolvedSection.sources` keeps the list, and
   the generator (feature 004) decides how to render it.
3. **Violations are values.** Checks return lists; the CLI prints them and sets the exit
   code. This lets the mutation experiment (feature 007) count detections per code.
4. **WF before S/C.** Dangling references are reported once, under WF, and the other
   checks skip what they cannot evaluate.
5. **Input narrowing is allowed in S4** (see spec edge cases); the type check moves to C2.

## Complexity Tracking

None.
