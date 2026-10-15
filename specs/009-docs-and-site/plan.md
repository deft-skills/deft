# Implementation Plan: Documentation and website

**Branch**: `009-docs-and-site` | **Spec**: [spec.md](spec.md)

## Summary

Markdown guides in `guides/`, and a static site generator that builds `docs/` from the
guides, sections of the README and the example library, served by GitHub Pages and by
the anonymous mirror during review.

## Technical Context

**Language/Version**: Python 3.11+ | **Dependencies**: none beyond `deft` and PyYAML
**Inputs**: `README.md`, `guides/*.md`, `models/`, `skills/`, `metamodel/*.svg`, `site/site.yaml`, `site/static/`
**Output**: `docs/` (committed; checked by CI)

## Constitution Check

- V. Reproducible evidence: CI fails if `docs/` differs from a fresh build. PASS
- VI. Small and dependency-light: the generator is plain Python, no site framework. PASS

## Project Structure

```text
guides/      # README, metamodel, modelling-guide, constraints, generation, using-skills, cli
site/
├── build.py     # pages, catalogue of skills/workflows/types, link rewriting
├── site.yaml    # navigation and URLs
└── static/      # app.js, style.css, logo
docs/        # built site
```

## Design decisions

1. **The README is a source.** Sections such as "Contributing" are read from the README,
   so the two cannot drift.
2. **Relative links rewritten at build time**, so the same Markdown works on GitHub,
   on Pages and on the anonymous mirror.
3. **The catalogue is generated from the models**, with resolved sections and diagrams.
