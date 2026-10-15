# Implementation Plan: Skill generation

**Branch**: `004-skill-generation` | **Spec**: [spec.md](spec.md)

## Summary

A model-to-text transformation in `deft/generate.py` that renders resolved skills
and executable workflows as `SKILL.md` folders, copies resources and licences, and
is validated with the reference validator `skills-ref`.

## Technical Context

**Language/Version**: Python 3.11+ (raised from 3.10 because `skills-ref` requires it)
**Primary Dependencies**: PyYAML (frontmatter); `skills-ref` (test only)
**Testing**: pytest + `skills-ref validate`
**CI**: regenerate `skills/` and fail on `git diff`

## Constitution Check

- I. Models in, standard skills out: output is plain Agent Skills; no DEFT runtime. PASS
- IV. Reference, do not copy: licences copied next to every derived skill. PASS
- V. Reproducible evidence: CI checks that `skills/` is up to date. PASS

## Design decisions

1. **DEFT data in `metadata` only.** The specification allows free keys under
   `metadata`; everything DEFT adds lives there (`deft-*`), so agents that ignore it lose nothing.
2. **Provenance as HTML comments.** Invisible in rendered Markdown, visible to people
   and agents reading the raw file.
3. **Workflows as instructions.** A workflow becomes a skill that lists its steps in
   topological order and names the skill and artifacts of each step; a Mermaid
   diagram goes in `references/`.
4. **Refuse ill-formed input.** `deft generate` runs `check_library` first.

## Project Structure

```text
deft/generate.py   # render_skill, render_workflow, topological_steps, mermaid, generate
upstream/          # pinned spec-kit, superpowers, anthropics/skills + UPSTREAM.yaml
skills/            # generated, committed, checked by CI
NOTICE
.github/workflows/ci.yml
tests/test_generate.py
```
