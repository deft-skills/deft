# CLI contract: `deft obligations`

```text
deft obligations <models> [--workflow NAME]
```

For each composite skill (or only `NAME`) and each obligation:

```text
## <workflow>: <predecessors> -> <node>
guarantees:
  - <postcondition, guard or workflow precondition>
must entail:
  - <precondition of node>
```

`(none)` is printed when a node has no guarantees. Exit code is always 0: obligations
are listed, never decided.
