# Feature Specification: Documentation and website

**Feature Branch**: `009-docs-and-site`
**Created**: 2026-10-07; updated with every later feature
**Status**: Implemented
**Input**: "Others must be able to learn DEFT step by step and browse the example library without installing anything. Publish a static site from the repository, also reachable through the anonymous mirror during review."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Learn DEFT step by step (Priority: P1)

A newcomer follows the README: understand the metamodel, write a model (a Planguage
exercise), validate it, generate skills, use them with an agent, browse the catalogue.

### User Story 2 - Browse the library (Priority: P1)

A visitor opens the site and browses every skill, workflow and artifact type, with
resolved sections and diagrams.

### User Story 3 - Contribute (Priority: P3)

A contributor finds how to report problems, add skills, change the tool and what to
run before a pull request (added on 2026-10-15).

## Requirements *(mandatory)*

- **FR-001**: Guides: `metamodel.md`, `modelling-guide.md`, `constraints.md`,
  `generation.md`, `using-skills.md`, `cli.md`.
- **FR-002**: `site/build.py` builds `docs/` from the guides, the README and the models.
- **FR-003**: CI fails if `docs/` is out of date.
- **FR-004**: Links work both on GitHub Pages and on the anonymous mirror.
