# Implementation Plan: Composition — C1–C4 and C5 obligations

**Branch**: `003-composition-checks` | **Spec**: [spec.md](spec.md)

## Summary

Extend `deft/check.py` with composition checks evaluated on the effective (bound)
skills, add an obligation generator for C5, and expose it as `deft obligations`.

## Technical Context

**Language/Version**: Python 3.11+ | **Dependencies**: none new | **Testing**: pytest

## Constitution Check

- II. Check before execution: C1–C4 decided; C5 listed for people, not decided. PASS
- III. One rule, three forms: OCL invariants C1–C4; C5 documented as a review step. PASS

## Design decisions

1. **Types at the binding site.** `_port_param` looks up the parameter on the node's
   effective skill, so narrowing allowed by S4 is caught here (C2).
2. **One edge checker** (`_check_edge_types`) for plain data edges and repair payloads.
3. **C4 by DFS** on the graph without repair edges; invoked nodes are checked
   separately (one caller, no other incoming control edge).
4. **Control nodes forward guarantees.** A decision or final node has no conditions of
   its own, so `guarantees(node, seen)` passes on what reaches it; skill nodes give their
   inherited postconditions. The workflow preconditions are assumed at every step, and
   one more obligation checks the workflow postconditions against what reaches `self`
   and the final node.
5. **`is_executable`** decides which workflows the generator (feature 004) writes.

## Project Structure

```text
deft/check.py   # _port_param, _check_edge_types, check_c1..c4, check_composite, is_executable, Obligation, obligations
deft/cli.py     # deft obligations
```

## Complexity Tracking

None.
