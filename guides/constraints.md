# Validating models

`deft check` reports violations with a code. S constraints apply to
hierarchies, C constraints to workflows. The OCL version is in
`metamodel/deft.ocl`; the implementation is `deft/check.py`.

| Code | Rule | Typical message |
|---|---|---|
| WF | Every reference resolves: parent, type, role, binding, node, parameter; a skill specializes a skill of its own kind (atomic or composite); edges leave outputs and enter inputs (an `inout` parameter is both); decisions have two or more guarded exits; a bundled resource lives in the folder of its kind (`scripts/`, `references/`, `assets/`); an `imported` origin and sections read from upstream files (`source:`) go together. | `node 'x' refers to unknown skill 'y'`; `script resource 'references/run.py' must live under scripts/` |
| S1 | Both hierarchies are acyclic; a skill or type has at most one parent. | `skill hierarchy is cyclic` |
| S2 | A concrete skill implements every abstract section it inherits. | `concrete skill leaves abstract section 'structure' ... unimplemented` |
| S3 | A refinement targets a section inherited from an ancestor, with the kind it has in the parent: `implements` an abstract section, `overrides`/`extends` a default one. Final sections, declared final or sealed by a refinement with `final: true`, admit no refinement; inherited sections are not redeclared. | `overrides targets final section 'elicit' (declared by specify-requirements)` |
| S4 | A redeclared parameter keeps its direction and narrows the inherited type; a property redeclared by a subtype narrows the inherited multiplicity. | `parameter 'requirements': Diagnosis does not specialize inherited Requirement`; `property 'fitCriterion' [0..1] widens inherited [1..1]` |
| C1 | A binding is concrete and specializes its role. | `node 'quality' is bound to abstract skill 'specify-quality'` |
| C2 | A data edge (or repair payload) is type-safe on the effective skills: `type(source) ⊑ type(target)`, and a many-valued source does not feed a single-valued input. | `EARSRequirement (from ears) does not conform to UserStory (required by acceptance-gherkin)` |
| C3 | Every mandatory input (`in` or `inout`) of a node receives a data edge (an invoked node may take it from its caller); every mandatory output of the workflow is produced. | `mandatory input plan.requirements (Requirement) receives no data edge` |
| C4 | Without repair edges the graph is acyclic; repair edges have a bound of at least 1; an invoked node has one caller and no other incoming control edge. | `the graph without repair edges is cyclic` |
| C5 | For every node, the postconditions of its predecessors and the guards that reach it, under the workflow's preconditions, entail its preconditions. | listed by `deft obligations`, not decided |

## Why input narrowing is allowed

S4 lets a descendant narrow an *input* type. Behavioural subtyping forbids
this, because a narrower input means a stronger precondition, and the
descendant is then no longer substitutable for its parent. Skill families need
it: an acceptance-test skill accepts only user stories, a load-test skill only
measurable quality requirements. DEFT therefore accepts the narrowing in the
hierarchy and moves the substitutability check to the place where it can be
decided: the binding of a node in a workflow (C1) and the edges around it (C2),
which are recomputed with the bound skills' types.

## C5 in practice

C5 is natural language. `deft obligations` lists, per node, the guarantees it
can rely on and the preconditions they must entail:

```text
## deliver-feature: plan, debug -> implement
guarantees:
  - The plan has at least one task.
  - Every requirement id is covered by at least one task.
  - Every task names its files, its interfaces and the test that proves it.
  - The diagnosis names a root cause supported by evidence, not a symptom.
must entail:
  - The plan has at least one task and every task names its test.
```

Review each obligation. When a precondition is not entailed, either a step is
missing, a postcondition is too weak, or the precondition is an assumption of the
whole workflow (declare it as a precondition of the composite skill). An optional
LLM judge for this review is provided in `experiments/c5_contracts/judge.py`.
