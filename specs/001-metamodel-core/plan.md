# Implementation Plan: Metamodel core

**Branch**: `001-metamodel-core` | **Spec**: [spec.md](spec.md)

## Summary

Implement the metamodel as Python dataclasses grouped in two packages, a YAML loader
that builds a `Library`, and an Ecore export of the same metamodel.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PyYAML
**Storage**: YAML files in a library folder
**Testing**: pytest
**Target Platform**: any OS with Python; CI on ubuntu-latest, Python 3.11 and 3.13
**Project Type**: single package (`deft/`)
**Constraints**: no runtime dependency beyond PyYAML (Constitution VI)

## Constitution Check

- I. Models in, standard skills out: the model is author-facing only. PASS
- III. One rule, three forms: no rules yet; the Ecore file is the second form of the metamodel. PASS
- VI. Small and dependency-light: dataclasses and PyYAML. PASS

## Project Structure

```text
deft/
├── __init__.py
├── __main__.py
├── model.py      # dataclasses, enumerations, Library helpers
└── loader.py     # YAML -> Library, ModelError
metamodel/
├── deft.ecore
├── deft-specialization.puml
└── deft-composition.puml
```

## Design decisions

1. **Dataclasses over a modelling framework.** PyEcore or EMF would give the
   metamodel for free but add a heavy dependency; the Ecore file is maintained by
   hand and kept in sync (Constitution III).
2. **Names as references.** Parents, types, roles and bindings are names, resolved
   lazily, so the loader never fails on a dangling reference; the checker reports it
   (WF).
3. **Nearest declaration wins** for inherited properties and parameters.
4. **One family per YAML file** (`family:` key) to mirror how skill libraries are
   organized in practice.

## Complexity Tracking

None.
