"""Agreement of C5 reviewers: LLM judges and people, against the reference review.

Reads results/c5_items.json (with the reference verdicts of the manual review),
results/c5_judges.json (judge.py) and human/answers/*.json (the review sheet).
For every reviewer: answered items, accuracy against the reference, gaps found
(of the obligations that do not hold), false alarms, whether the uncovered
requirements named match the reference, and Cohen's kappa. Kappa is also given for
every pair of reviewers.

Output: results/c5_agreement.json and results/c5_agreement.md
"""
from __future__ import annotations

import glob
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from common import RESULTS, save  # noqa: E402

LABELS = ("entailed", "not-entailed")


def kappa(a: list[str], b: list[str]) -> float | None:
    pairs = [(x, y) for x, y in zip(a, b) if x in LABELS and y in LABELS]
    if not pairs:
        return None
    n = len(pairs)
    po = sum(x == y for x, y in pairs) / n
    pe = sum((sum(x == l for x, _ in pairs) / n) * (sum(y == l for _, y in pairs) / n) for l in LABELS)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else (1.0 if po == 1 else None)


def reviewers(items: list[dict]) -> dict[str, dict]:
    from judge import items_digest
    out = {}
    path = os.path.join(RESULTS, "c5_judges.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            judges = json.load(fh)
        if judges.pop("items_digest", None) != items_digest(items):
            raise SystemExit("c5_judges.json was produced for other items: rerun judge.py")
        for name, d in judges.items():
            out[f"{name} ({d['model']})"] = d["answers"]
    for f in sorted(glob.glob(os.path.join(HERE, "human", "answers", "*.json"))):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        out[f"human {d.get('rater') or os.path.basename(f)[:-5]}"] = d["answers"]
    return out


def main() -> dict:
    with open(os.path.join(RESULTS, "c5_items.json"), encoding="utf-8") as fh:
        items = json.load(fh)
    ref = {i["id"]: i for i in items}
    ids = [i["id"] for i in items]
    gaps = [i for i in ids if ref[i]["reference"] == "not-entailed"]
    holds = [i for i in ids if ref[i]["reference"] == "entailed"]
    revs = reviewers(items)
    per = {}
    for name, ans in revs.items():
        v = {i: (ans.get(i) or {}).get("verdict") for i in ids}
        answered = [i for i in ids if v[i] in LABELS]
        per[name] = {
            "answered": len(answered),
            "unsure_or_missing": len(ids) - len(answered),
            "accuracy": round(sum(v[i] == ref[i]["reference"] for i in ids) / len(ids), 3),
            "gaps_found": f"{sum(v[i] == 'not-entailed' for i in gaps)}/{len(gaps)}",
            "false_alarms": f"{sum(v[i] == 'not-entailed' for i in holds)}/{len(holds)}",
            "uncovered_match": f"{sum(v[i] == 'not-entailed' and set((ans.get(i) or {}).get('uncovered') or []) == set(ref[i]['reference_uncovered']) for i in gaps)}/{len(gaps)}",
            "kappa_vs_reference": kappa([v[i] for i in ids], [ref[i]["reference"] for i in ids]),
        }
    pairs = {}
    for a, b in itertools.combinations(revs, 2):
        va = [(revs[a].get(i) or {}).get("verdict") for i in ids]
        vb = [(revs[b].get(i) or {}).get("verdict") for i in ids]
        pairs[f"{a} vs {b}"] = kappa(va, vb)
    result = {"items": len(ids), "reference_gaps": len(gaps), "reviewers": per, "pairwise_kappa": pairs}
    lines = ["# C5 review agreement", "",
             f"{len(ids)} obligations of deliver-feature (before and after the contract fixes); "
             f"{len(gaps)} do not hold in the reference review.", "",
             "| Reviewer | Answered | Accuracy | Gaps found | False alarms | Uncovered named right | Kappa vs reference |",
             "|---|---|---|---|---|---|---|"]
    for name, d in per.items():
        lines.append(f"| {name} | {d['answered']} | {d['accuracy']} | {d['gaps_found']} | {d['false_alarms']} | "
                     f"{d['uncovered_match']} | {d['kappa_vs_reference']} |")
    if pairs:
        lines += ["", "| Pair | Kappa |", "|---|---|"] + [f"| {p} | {k} |" for p, k in pairs.items()]
    save("c5_agreement.json", result)
    save("c5_agreement.md", "\n".join(lines) + "\n")
    return result


if __name__ == "__main__":
    r = main()
    print(open(os.path.join(RESULTS, "c5_agreement.md"), encoding="utf-8").read())
