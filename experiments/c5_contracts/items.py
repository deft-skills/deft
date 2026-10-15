"""C5 review items: the contract obligations of deliver-feature, before and after review.

The first version of the models had three contract gaps, found in the manual review
recorded in review.yaml and then fixed. This script rebuilds that first version from
the current models and lists the obligations of both versions, each with the reference
verdict of the manual review and with its guarantees grouped by where they come from.
The models were improved again after these items were reviewed (REVIEWED); the
items keep the conditions as they were reviewed, so the answers stay valid.

Items are presented in two rounds. Each round contains one version of every step, in
workflow order; which version falls in which round is random per step (fixed seed).
Reviewers are not told the version, and never see both versions of a step side by
side.

Output: results/c5_items.json
"""
from __future__ import annotations

import copy
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import MODELS, save  # noqa: E402

from deft.check import obligations  # noqa: E402
from deft.loader import load_library  # noqa: E402
from deft.model import ControlEdgeKind, ControlNode, SkillNode  # noqa: E402

WORKFLOW = "deliver-feature"
SEED = 7

# Steps in workflow order, with the plain-language label shown to reviewers.
STEPS = [
    ("functional", "specify the functional requirements as user stories"),
    ("quality", "specify the quality requirements as Volere snow cards"),
    ("plan", "plan the implementation as test-first tasks"),
    ("implement", "implement the plan task by task, test-first"),
    ("acceptance", "write and run acceptance tests for the user stories"),
    ("performance", "write and run load tests for the quality requirements"),
    ("debug", "diagnose the failing tests"),
    ("self", "end of the workflow: what it promises to whoever started it"),
]
NUMBER = {sid: i + 1 for i, (sid, _) in enumerate(STEPS) if sid != "self"}
LABEL = dict(STEPS)

# The three conditions as they were before the review (see review.yaml).
BEFORE = {
    "execute-plan.post": ["Every task is committed and its tests pass.",
                          "Every deviation from the plan is recorded as a ruling."],
    "performance-tests.pre": ["A deployment of the system that matches production in configuration is available."],
    "deliver-feature.pre": ["The feature request names the existing system and its stack."],
}

# Steps whose obligation did not hold before the review, and the preconditions at stake.
GAPS = {
    "acceptance": ["The code builds and its existing tests pass."],
    "performance": ["The code builds and its existing tests pass.",
                    "A deployment of the system that matches production in configuration is available."],
    "self": ["The code is committed on a feature branch."],
}


# Conditions changed after the review of these items by a second reviewer and the
# LLM judges (round 3 of review.yaml): the items show them as they were reviewed.
REVIEWED = {
    "plan-feature.post": ["Every requirement id is covered by at least one task.",
                          "Every task names its files, its interfaces and the test that proves it."],
    "execute-plan.post": ["Every task is committed on the dedicated branch.",
                          "The full test suite passes, including the tests that existed before.",
                          "Every deviation from the plan is recorded as a ruling."],
}


def library_reviewed(lib):
    old = copy.deepcopy(lib)
    for key, conds in REVIEWED.items():
        skill, attr = key.split(".")
        setattr(old.skills[skill], attr, list(conds))
    return old


def library_before(lib):
    old = library_reviewed(lib)
    old.skills["execute-plan"].post = list(BEFORE["execute-plan.post"])
    old.skills["performance-tests"].pre = list(BEFORE["performance-tests.pre"])
    old.skills[WORKFLOW].pre = list(BEFORE["deliver-feature.pre"])
    return old


def sources(lib, comp, target: str) -> list[dict]:
    """Guarantees of a step, grouped by where they come from."""
    groups: list[dict] = []

    def add(origin: str, conds):
        conds = [c for c in conds if c]
        if not conds:
            return
        for g in groups:
            if g["from"] == origin:
                g["conditions"] += [c for c in conds if c not in g["conditions"]]
                return
        groups.append({"from": origin, "conditions": list(conds)})

    def from_node(node_id: str, repair: bool = False, seen=frozenset()):
        node = comp.node(node_id)
        if isinstance(node, SkillNode):
            when = " (when the workflow comes back here after a failure)" if repair else ""
            add(f"Guaranteed by step {NUMBER[node_id]}, {LABEL[node_id]}{when}",
                lib.effective_conditions(node.effective)[1])
        elif isinstance(node, ControlNode) and node_id not in seen:
            for c in comp.control:
                if c.target == node_id:
                    from_node(c.source, seen=seen | {node_id})

    incoming = [(e.source.node, None, None) for e in comp.data if e.target.node == target]
    incoming += [(c.source, c.guard, c.kind) for c in comp.control if c.target == target]
    if target == "self":
        for n in comp.nodes:
            if isinstance(n, ControlNode) and n.kind.value == "final":
                incoming += [(c.source, c.guard, c.kind) for c in comp.control if c.target == n.name]
    for src, guard, kind in incoming:
        if src == "self":
            continue
        from_node(src, repair=kind == ControlEdgeKind.REPAIR)
        if guard:
            add("Condition under which the workflow reaches this point", [guard])
    add("Assumed by the whole workflow", comp.pre)
    return groups


def build() -> list[dict]:
    lib = load_library(MODELS)
    per_step: dict[str, dict[str, dict]] = {sid: {} for sid, _ in STEPS}
    for version, library in (("before", library_before(lib)), ("after", library_reviewed(lib))):
        comp = library.skills[WORKFLOW]
        for o in obligations(library, comp):
            groups = sources(library, comp, o.target)
            flat = [c for g in groups for c in g["conditions"]]
            assert set(flat) == set(o.post), (o.target, set(flat) ^ set(o.post))
            gap = version == "before" and o.target in GAPS
            per_step[o.target][version] = {
                "version": version,
                "target": o.target,
                "step": LABEL[o.target],
                "number": NUMBER.get(o.target),
                "guarantees": o.post,
                "guarantee_sources": groups,
                "requires": o.pre,
                "reference": "not-entailed" if gap else "entailed",
                "reference_uncovered": list(GAPS[o.target]) if gap else [],
            }
    # Counterbalance: the first seed from SEED on that puts 4 items of each version in
    # each round and splits the obligations that do not hold across both rounds.
    seed = SEED
    while True:
        rng = random.Random(seed)
        rounds = ([], [])
        for sid, _ in STEPS:
            pair = [per_step[sid]["before"], per_step[sid]["after"]]
            rng.shuffle(pair)
            rounds[0].append(pair[0])
            rounds[1].append(pair[1])
        balanced = all(sum(i["version"] == "before" for i in r) == len(STEPS) // 2 for r in rounds)
        split = all(any(i["reference"] == "not-entailed" for i in r) for r in rounds)
        if balanced and split:
            break
        seed += 1
    items = []
    for r, rnd in enumerate(rounds, start=1):
        for it in rnd:
            it["round"] = r
            items.append(it)
    for i, it in enumerate(items, start=1):
        it["id"] = f"O{i:02d}"
    return items


def main() -> list[dict]:
    items = build()
    save("c5_items.json", items)
    return items


if __name__ == "__main__":
    items = main()
    print(len(items), "items in 2 rounds;", sum(i["reference"] == "not-entailed" for i in items),
          "not entailed in the reference")
    for it in items:
        print(it["id"], it["round"], it["target"], it["version"], it["reference"],
              [g["from"][:40] for g in it["guarantee_sources"]])
