"""Run every experiment and write results/summary.md.

    python experiments/run_all.py

No API key is needed; the tokenizer encoding is downloaded once on first use.
The LLM judges of C5 need API keys and run separately:
python experiments/c5_contracts/judge.py (see experiments/README.md)
"""
from __future__ import annotations

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import save  # noqa: E402


def _run(rel: str):
    path = os.path.join(HERE, rel)
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location(os.path.basename(rel)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main()


def main() -> None:
    survey = _run("e1_expressiveness/survey.py")
    speckit = _run("e1_expressiveness/refactor_speckit.py")
    mutation = _run("e2_checkability/mutate.py")
    configs = _run("e2_checkability/configurations.py")
    generation = _run("e3_generation/measure.py")
    c5 = _run("c5_contracts/obligations.py")

    sk, sp = survey["spec-kit"], survey["superpowers"]
    cov = survey["coverage"]
    lines = ["# Results summary", "",
             "## E1 Expressiveness", "",
             f"- Conventions mapped: {cov['conventions']} (full {cov['full']}, partial {cov['partial']}, none {cov['none']}).",
             f"- spec-kit: {sk['skills']} commands, {sk['handoff_edges']} handoff edges, "
             f"{sk['skills_with_pre_execution_checks']} with Pre-Execution Checks, {sk['skills_with_done_when']} with Done When.",
             f"- superpowers: {sp['skills']} skills, {sp['prose_reference_edges']} prose references between skills, "
             f"{sp['embedded_dot_graphs']} embedded DOT graphs in {sp['skills_with_dot_graphs']} skills.",
             f"- spec-kit as a DEFT family: {speckit['upstream_nonblank_lines']} upstream lines -> "
             f"{speckit['deft_authored_lines']} authored lines ({speckit['reduction']:.1%} fewer); "
             f"{speckit['upstream_tokens']} -> {speckit['deft_authored_tokens']} tokens "
             f"({speckit['token_reduction']:.1%} fewer, {speckit['tokenizer']}); "
             f"round trip identical for {speckit['round_trip_identical']}/{speckit['commands']} commands; "
             f"{len(speckit['violations'])} violations.",
             ""]
    for h, d in speckit["factored_sections"].items():
        drift = f", drifted: {', '.join(d['drifted_copies'])}" if d["drifted_copies"] else ""
        lines.append(f"  - {h}: {d['copies']} copies -> 1 section of {d['template_lines']} lines, {d['slots']} slots{drift}")
    t = mutation["total"]
    lines += ["", "## E2 Checkability", "",
              f"- Baseline violations on the unmutated library: {len(mutation['baseline_violations'])}.",
              f"- Mutants: {t['mutants']}; killed {t['killed']}; reported under the intended constraint {t['intended']}; "
              f"only under it {t['exclusive']}.", "",
              "| Constraint | Mutants | Killed | Intended | Exclusive |", "|---|---|---|---|---|"]
    for c, d in mutation["by_constraint"].items():
        lines.append(f"| {c} | {d['mutants']} | {d['killed']} | {d['intended']} | {d['exclusive']} |")
    lines.append("")
    for w, d in configs.items():
        lines.append(f"- {w}: {d['valid']}/{d['configurations']} binding configurations well formed; "
                     f"rejections by code: {d['violations_by_code']}.")
    lines += ["", "## E3 Generation", "",
              f"- Skills in the models: {generation['skills_in_models']} ({generation['abstract_skills']} abstract); "
              f"generated: {generation['generated_skills']}.",
              f"- Authored instruction lines: {generation['authored']['instruction_lines']} "
              f"(+{generation['authored']['imported_lines']} imported verbatim); "
              f"generated SKILL.md lines: {generation['generated_nonblank_lines']}.",
              f"- Tokens ({generation['tokenizer']}): authored {generation['authored']['instruction_tokens']}, "
              f"imported {generation['authored']['imported_tokens']}, generated {generation['generated_tokens']}.",
              f"- Lines repeated across generated skills: {generation['distinct_repeated_lines']} distinct, "
              f"{generation['repeated_line_copies']} extra copies ({generation['repeated_copy_tokens']} tokens).",
              f"- skills-ref validation: {generation['skills_ref_pass']}/{generation['generated_skills']} pass.",
              "", "## C5 Contracts", ""]
    for w, obs in c5.items():
        lines.append(f"- {w}: {len(obs)} obligations (see c5_obligations.md and c5_contracts/review.yaml).")
    save("summary.md", "\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
