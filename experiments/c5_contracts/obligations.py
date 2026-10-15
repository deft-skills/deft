"""C5: contract obligations post(m) |= pre(n) along every edge m -> n.

C5 relates natural-language conditions and is not decided by the checker.
This script lists every obligation of the workflows for review. With
the review of the obligations by people and LLM judges is in items.py, judge.py,
the human/ sheet and analyse.py.

Output: results/c5_obligations.json and results/c5_obligations.md
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import MODELS, save  # noqa: E402

from deft.check import obligations  # noqa: E402
from deft.loader import load_library  # noqa: E402
from deft.model import CompositeSkill  # noqa: E402


def main() -> dict:
    lib = load_library(MODELS)
    data = {}
    md = ["# C5 obligations", "",
          "For every node `n`, the postconditions of its predecessors and the guards that reach it must jointly entail the preconditions of `n`.", ""]
    for name, wf in sorted(lib.skills.items()):
        if not isinstance(wf, CompositeSkill):
            continue
        obs = obligations(lib, wf)
        data[name] = [dict(o.__dict__, edge=o.edge) for o in obs]
        md += [f"## {name}", ""]
        for o in obs:
            md.append(f"### {o.target} (from {', '.join(o.sources)})")
            md.append("")
            md.append("Guarantees:")
            md += [f"- {c}" for c in (o.post or ["(none)"])]
            md.append("")
            md.append("Must entail:")
            md += [f"- {c}" for c in o.pre]
            md.append("")
    save("c5_obligations.json", data)
    save("c5_obligations.md", "\n".join(md) + "\n")
    return data


if __name__ == "__main__":
    d = main()
    for w, obs in d.items():
        print(w, len(obs), "obligations,", sum(1 for o in obs if not o["post"]), "with no postcondition at the source")
