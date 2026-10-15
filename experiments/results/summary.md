# Results summary

## E1 Expressiveness

- Conventions mapped: 14 (full 9, partial 3, none 2).
- spec-kit: 10 commands, 8 handoff edges, 10 with Pre-Execution Checks, 5 with Done When.
- superpowers: 15 skills, 20 prose references between skills, 8 embedded DOT graphs in 6 skills.
- spec-kit as a DEFT family: 1817 upstream lines -> 1410 authored lines (22.4% fewer); 29600 -> 23572 tokens (20.4% fewer, o200k_base); round trip identical for 10/10 commands; 0 violations.

  - User Input: 10 copies -> 1 section of 4 lines, 0 slots
  - Pre-Execution Checks: 10 copies -> 1 section of 28 lines, 3 slots, drifted: converge
  - Post-Execution Checks: 3 copies -> 1 section of 27 lines, 2 slots
  - Mandatory Post-Execution Hooks: 5 copies -> 1 section of 27 lines, 2 slots

## E2 Checkability

- Baseline violations on the unmutated library: 0.
- Mutants: 311; killed 311; reported under the intended constraint 311; only under it 252.

| Constraint | Mutants | Killed | Intended | Exclusive |
|---|---|---|---|---|
| T1 | 19 | 19 | 19 | 19 |
| T2 | 10 | 10 | 10 | 10 |
| T3 | 105 | 105 | 105 | 105 |
| T4 | 41 | 41 | 41 | 31 |
| WF | 40 | 40 | 40 | 16 |
| C1 | 25 | 25 | 25 | 4 |
| C2 | 25 | 25 | 25 | 21 |
| C3 | 19 | 19 | 19 | 19 |
| C4 | 27 | 27 | 27 | 27 |

- deliver-feature: 4/16 binding configurations well formed; rejections by code: {'C2': 16}.
- deliver-feature-iso: 4/16 binding configurations well formed; rejections by code: {'C2': 16}.

## E3 Generation

- Skills in the models: 21 (6 abstract); generated: 15.
- Authored instruction lines: 198 (+457 imported verbatim); generated SKILL.md lines: 1246.
- Tokens (o200k_base): authored 2732, imported 4456, generated 13858.
- Lines repeated across generated skills: 135 distinct, 283 extra copies (3583 tokens).
- skills-ref validation: 15/15 pass.

## C5 Contracts

- deliver-feature: 8 obligations (see c5_obligations.md and c5_contracts/review.yaml).
- deliver-feature-iso: 8 obligations (see c5_obligations.md and c5_contracts/review.yaml).
