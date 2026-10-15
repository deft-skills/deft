"""E2 (checkability): the binding space of the workflow templates.

Every role of a workflow is bound, in turn, to every concrete skill that
specializes it. The checker decides which configurations are well formed;
the rejected ones would otherwise fail, at best, while an agent runs them.

Output: results/e2_configurations.json
"""
from __future__ import annotations

import collections
import copy
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import MODELS, save  # noqa: E402

from deft.check import check_library  # noqa: E402
from deft.loader import load_library  # noqa: E402
from deft.model import CompositeSkill  # noqa: E402


def candidates(lib, role):
    return sorted(n for n, s in lib.skills.items()
                  if not s.abstract and not isinstance(s, CompositeSkill) and lib.conforms_skill(n, role))


def main() -> dict:
    base = load_library(MODELS)
    out = {}
    for wname in ("deliver-feature", "deliver-feature-iso"):
        wf = base.skills[wname]
        variable = [(n.name, candidates(base, n.role)) for n in wf.skill_nodes() if len(candidates(base, n.role)) > 1]
        configs, reasons = [], collections.Counter()
        for combo in itertools.product(*[c for _, c in variable]):
            lib = copy.deepcopy(base)
            for (nid, _), skill in zip(variable, combo):
                lib.skills[wname].node(nid).bind = skill
            found = [v for v in check_library(lib) if v.element == f"workflow {wname}"]
            ok = not found
            for v in found:
                reasons[v.code] += 1
            configs.append({"binding": dict(zip([n for n, _ in variable], combo)), "valid": ok,
                            "violations": [str(v) for v in found]})
        out[wname] = {"variation_points": {n: c for n, c in variable}, "configurations": len(configs),
                      "valid": sum(c["valid"] for c in configs), "violations_by_code": dict(reasons),
                      "details": configs}
    save("e2_configurations.json", out)
    return out


if __name__ == "__main__":
    r = main()
    for w, d in r.items():
        print(w, d["variation_points"], f"{d['valid']}/{d['configurations']} valid", d["violations_by_code"])
