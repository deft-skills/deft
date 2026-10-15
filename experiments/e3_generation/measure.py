"""E3 (generation): what the model-to-text transformation produces.

For the running example: authored instruction lines in the models versus
lines in the generated SKILL.md files, lines that the generated files repeat
(content a hand-maintained library would have to keep in sync), and
conformance of every generated skill to the Agent Skills specification
(skills-ref reference validator).

Output: results/e3_generation.json
"""
from __future__ import annotations

import collections
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import MODELS, TOKENIZER, nonblank, save, split_frontmatter, tokens  # noqa: E402

from deft.generate import generate  # noqa: E402
from deft.loader import load_library  # noqa: E402
from deft.model import OriginMode  # noqa: E402

try:
    from skills_ref.validator import validate
except ImportError:  # pragma: no cover
    validate = None


def authored(lib) -> dict:
    """Non-blank instruction lines written in the models (imports excluded)."""
    own = imported = conditions = own_tok = imported_tok = 0
    for s in lib.skills.values():
        imported_skill = any(o.mode == OriginMode.IMPORTED for o in s.origin)
        for sec in getattr(s, "sections", []):
            n, t = nonblank(sec.content.splitlines()), tokens(sec.content)
            if imported_skill:
                imported, imported_tok = imported + n, imported_tok + t
            else:
                own, own_tok = own + n, own_tok + t
        for r in getattr(s, "refinements", []):
            own += nonblank(r.content.splitlines())
            own_tok += tokens(r.content)
        conditions += len(s.pre) + len(s.post)
    return {"instruction_lines": own, "imported_lines": imported, "conditions": conditions,
            "instruction_tokens": own_tok, "imported_tokens": imported_tok}


def main() -> dict:
    lib = load_library(MODELS)
    with tempfile.TemporaryDirectory() as out:
        names = generate(lib, out, provenance=False)
        lines_per_skill, counter, generated_tok = {}, collections.Counter(), 0
        errors = {}
        for n in names:
            with open(os.path.join(out, n, "SKILL.md"), encoding="utf-8") as fh:
                _, body = split_frontmatter(fh.read())
            body_lines = [l.strip() for l in body.splitlines() if l.strip()]
            generated_tok += tokens(body)
            lines_per_skill[n] = len(body_lines)
            # count each distinct instruction line once per skill (headings excluded)
            for l in set(body_lines):
                if not l.startswith("#") and len(l) > 20:
                    counter[l] += 1
            if validate is not None:
                e = validate(os.path.join(out, n))
                if e:
                    errors[n] = e
    repeated = {l: c for l, c in counter.items() if c > 1}
    a = authored(lib)
    generated = sum(lines_per_skill.values())
    result = {
        "skills_in_models": len(lib.skills),
        "abstract_skills": sum(s.abstract for s in lib.skills.values()),
        "generated_skills": len(names),
        "authored": a,
        "generated_nonblank_lines": generated,
        "tokenizer": TOKENIZER,
        "generated_tokens": generated_tok,
        "lines_per_generated_skill": lines_per_skill,
        "distinct_repeated_lines": len(repeated),
        "repeated_line_copies": sum(c - 1 for c in repeated.values()),
        "repeated_copy_tokens": sum(tokens(l) * (c - 1) for l, c in repeated.items()),
        "skills_ref_checked": validate is not None,
        "skills_ref_errors": errors,
        "skills_ref_pass": len(names) - len(errors) if validate is not None else None,
    }
    save("e3_generation.json", result)
    return result


if __name__ == "__main__":
    r = main()
    print({k: v for k, v in r.items() if k != "lines_per_generated_skill"})
