"""Build the human review sheet for the C5 items: one self-contained HTML file.

    python experiments/c5_contracts/make_sheet.py

Writes human/c5-review-sheet.html. Send that single file to a reviewer; it works
offline, saves answers in the browser while the reviewer works, and downloads them as
a JSON file to send back (store it in human/answers/). Cards show no version and no
reference verdict. The definitions and the workflow overview are the same text the LLM
judges receive (review_text.py).
"""
from __future__ import annotations

import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from common import RESULTS  # noqa: E402
from review_text import DEFINITIONS, OVERVIEW  # noqa: E402

E = html.escape
OUT = os.path.join(HERE, "human", "c5-review-sheet.html")
STEPS_TOTAL = 7

DIAGRAM = """<svg viewBox="0 0 790 280" role="img" aria-label="Workflow diagram" style="width:100%;height:auto">
<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker></defs>
<style>.b{fill:#fff;stroke:#333;stroke-width:1.2}.t{font:600 12px system-ui,sans-serif;fill:#1a1a1a}
.s{font:11px system-ui,sans-serif;fill:#555}.e{stroke:#333;stroke-width:1.2;fill:none;marker-end:url(#a)}
.d{stroke-dasharray:5 4}.l{font:11px system-ui,sans-serif;fill:#555}</style>
<circle cx="18" cy="118" r="8" class="b"/><text x="4" y="146" class="l">request</text>
<rect x="50" y="40" width="140" height="46" rx="8" class="b"/><text x="60" y="59" class="t">1 Specify functional</text><text x="60" y="76" class="s">user stories</text>
<rect x="50" y="150" width="140" height="46" rx="8" class="b"/><text x="60" y="169" class="t">2 Specify quality</text><text x="60" y="186" class="s">Volere snow cards</text>
<rect x="225" y="95" width="110" height="46" rx="8" class="b"/><text x="236" y="114" class="t">3 Plan</text><text x="236" y="131" class="s">test-first tasks</text>
<rect x="370" y="95" width="125" height="46" rx="8" class="b"/><text x="381" y="114" class="t">4 Implement</text><text x="381" y="131" class="s">test-first, per task</text>
<rect x="530" y="40" width="130" height="46" rx="8" class="b"/><text x="541" y="59" class="t">5 Acceptance tests</text><text x="541" y="76" class="s">user stories</text>
<rect x="530" y="150" width="130" height="46" rx="8" class="b"/><text x="541" y="169" class="t">6 Load tests</text><text x="541" y="186" class="s">quality requirements</text>
<path d="M705,104 L719,118 L705,132 L691,118 z" class="b"/><text x="676" y="96" class="l">all pass?</text>
<circle cx="770" cy="118" r="9" class="b"/><circle cx="770" cy="118" r="5" fill="#333"/><text x="756" y="146" class="l">end</text>
<rect x="530" y="225" width="130" height="42" rx="8" class="b"/><text x="541" y="244" class="t">7 Diagnose</text><text x="541" y="259" class="s">failing tests</text>
<path class="e" d="M25,113 L50,66"/><path class="e" d="M25,123 L50,170"/>
<path class="e" d="M190,63 L225,110"/><path class="e" d="M190,173 L225,126"/>
<path class="e" d="M335,118 L370,118"/>
<path class="e" d="M495,110 L530,66"/><path class="e" d="M495,126 L530,170"/>
<path class="e" d="M660,63 L695,111"/><path class="e" d="M660,173 L695,125"/>
<path class="e" d="M719,118 L760,118"/><text x="726" y="111" class="l">yes</text>
<path class="e" d="M705,132 L705,246 L660,246"/><text x="711" y="200" class="l">no</text>
<path class="e d" d="M530,246 L432,246 L432,141"/><text x="440" y="238" class="l">repair (≤ 3)</text>
</svg>"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DEFT contract review</title>
<style>
:root {{ --fg:#1a1a1a; --soft:#555; --line:#e2e2e2; --bg:#fff; --card:#fafafa; --acc:#1a1a1a; --bad:#b91c1c; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--fg); background:var(--bg); }}
main {{ max-width: 800px; margin: 0 auto; padding: 32px 16px 120px; }}
h1 {{ font-size: 1.7rem; margin: 0 0 4px; }} h2 {{ font-size: 1.2rem; margin: 36px 0 8px; }}
.lead {{ color: var(--soft); margin-top: 0; }}
.box {{ border:1px solid var(--line); border-radius:12px; padding:14px 18px; background:var(--card); margin:14px 0; }}
dl {{ margin:0; }} dt {{ font-weight:650; margin-top:8px; }} dd {{ margin:0 0 4px; }}
.card {{ border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin:18px 0; }}
.card.done {{ border-color:#aaa; }}
.tag {{ font: 600 .75rem/1 system-ui; color:var(--soft); letter-spacing:.04em; text-transform:uppercase; }}
.step {{ font-weight:650; font-size:1.05rem; margin:6px 0 10px; }}
.cols {{ display:grid; grid-template-columns: 1.3fr 1fr; gap:16px; }}
.cols h3 {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; color:var(--soft); margin:0 0 4px; }}
.src {{ font-size:.85rem; color:var(--soft); margin:8px 0 2px; font-style: italic; }}
ul {{ margin:0; padding-left: 18px; }} li {{ margin: 3px 0; }}
.choices {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }}
.choices label {{ border:1px solid var(--line); border-radius:999px; padding:6px 14px; cursor:pointer; user-select:none; }}
.choices input {{ display:none; }}
.choices label:has(input:checked) {{ border-color: var(--acc); background:#f1f1f1; font-weight:650; }}
.which {{ margin-top:10px; display:none; }} .which.show {{ display:block; }}
.which label {{ display:block; margin:4px 0; }}
textarea {{ width:100%; min-height:44px; margin-top:10px; border:1px solid var(--line); border-radius:8px; padding:8px; font:inherit; }}
input[type=text] {{ border:1px solid var(--line); border-radius:8px; padding:8px 10px; font:inherit; width: 260px; max-width:100%; }}
.bar {{ position:fixed; left:0; right:0; bottom:0; background:#fff; border-top:1px solid var(--line); padding:10px 16px; }}
.bar .in {{ max-width:800px; margin:0 auto; display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
button {{ font:inherit; border:1px solid var(--acc); background:var(--acc); color:#fff; border-radius:8px; padding:8px 14px; cursor:pointer; }}
button.ghost {{ background:#fff; color:var(--acc); }}
.ex .verdict {{ color: var(--bad); font-weight:650; }}
pre.ov {{ white-space: pre-wrap; font: inherit; margin: 8px 0 0; color: var(--soft); }}
@media (max-width: 680px) {{ .cols {{ grid-template-columns: 1fr; }} }}
</style></head>
<body><main>
<h1>Contract review</h1>
<p class="lead">About 15 to 20 minutes: {n} short cards, in two rounds. Your answers are saved in this browser
as you go; at the end, press <b>Download my answers</b> and send the file back.</p>

<h2>1. The workflow</h2>
<p>A coding agent delivers a feature request in an existing system by following a workflow of steps. Each step is
carried out with one <i>skill</i>, a document of instructions for the agent.</p>
<div class="box">{diagram}<pre class="ov">{overview}</pre></div>

<h2>2. What you decide</h2>
<p>Each skill states what it <b>requires</b> before it can start, and what it <b>guarantees</b> when it finishes.
For every card, decide: <b>do the guarantees listed on the card ensure every requirement of the step?</b></p>
<div class="box"><dl>{definitions}</dl></div>
<div class="box ex">
<div class="tag">Example</div>
<div class="step">Step: deploy the service</div>
<div class="cols"><div><h3>Guarantees</h3><div class="src">Guaranteed by the testing step:</div><ul><li>All tests pass.</li>
<li>The code is committed on a branch.</li></ul></div>
<div><h3>Requirements of the step</h3><ul><li>The code is committed on a branch.</li><li>A server with credentials is available.</li></ul></div></div>
<p>Answer: <span class="verdict">Not ensured</span>. Nothing guarantees a server with credentials, so you would tick
that requirement. If every requirement followed from the guarantees, you would answer <b>Ensured</b>. Use <b>Unsure</b>
when you cannot decide. There are no answers to look up: judge from the card and common sense only.</p>
</div>
<p>Your initials (only to tell reviewers apart): <input type="text" id="rater" placeholder="e.g. AB"></p>

{rounds}
</main>
<div class="bar"><div class="in"><span id="progress"></span><span style="flex:1"></span>
<button class="ghost" id="clear">Clear answers</button><button id="download">Download my answers</button></div></div>
<script>
const KEY = "deft-c5-review-v2";
const ITEMS = {ids};
function load() {{ try {{ return JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{ return {{}}; }} }}
function store(s) {{ try {{ localStorage.setItem(KEY, JSON.stringify(s)); }} catch (e) {{ /* storage unavailable */ }} }}
let state = load();
function collect() {{
  const out = {{ rater: document.getElementById("rater").value.trim(), answers: {{}} }};
  for (const id of ITEMS) {{
    const card = document.getElementById(id);
    const v = card.querySelector("input[name=v-" + id + "]:checked");
    const unc = [...card.querySelectorAll(".which input:checked")].map(x => x.value);
    out.answers[id] = {{ verdict: v ? v.value : null, uncovered: unc, comment: card.querySelector("textarea").value.trim() }};
  }}
  return out;
}}
function refresh() {{
  let done = 0;
  for (const id of ITEMS) {{
    const card = document.getElementById(id);
    const v = card.querySelector("input[name=v-" + id + "]:checked");
    card.classList.toggle("done", !!v);
    card.querySelector(".which").classList.toggle("show", !!v && v.value === "not-entailed");
    if (v) done++;
  }}
  document.getElementById("progress").textContent = done + " of " + ITEMS.length + " answered";
}}
function save() {{ state = collect(); store(state); refresh(); }}
function restore() {{
  document.getElementById("rater").value = state.rater || "";
  for (const [id, a] of Object.entries(state.answers || {{}})) {{
    const card = document.getElementById(id); if (!card) continue;
    if (a.verdict) {{ const r = card.querySelector("input[name=v-" + id + "][value=" + a.verdict + "]"); if (r) r.checked = true; }}
    for (const x of card.querySelectorAll(".which input")) x.checked = (a.uncovered || []).includes(x.value);
    card.querySelector("textarea").value = a.comment || "";
  }}
}}
document.addEventListener("input", save); document.addEventListener("change", save);
document.getElementById("download").addEventListener("click", () => {{
  const data = collect(); data.downloaded = new Date().toISOString();
  const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: "application/json" }});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "c5-answers-" + (data.rater || "reviewer") + ".json"; a.click();
}});
document.getElementById("clear").addEventListener("click", () => {{
  if (!confirm("Clear all answers in this browser?")) return;
  store({{}}); state = {{}}; for (const i of document.querySelectorAll("input")) {{ if (i.type === "text") i.value = ""; else i.checked = false; }}
  for (const t of document.querySelectorAll("textarea")) t.value = ""; refresh();
}});
restore(); refresh();
</script>
</body></html>
"""

ROUND = """<h2>{title}</h2>
<p>{intro}</p>
{cards}"""

CARD = """<section class="card" id="{id}">
<div class="tag">Card {num} of {n}</div>
<div class="step">{title}</div>
<div class="cols"><div><h3>Guarantees</h3>{guarantees}</div>
<div><h3>Requirements of the step</h3><ul>{requires}</ul></div></div>
<div class="choices">
<label><input type="radio" name="v-{id}" value="entailed"><span>Ensured</span></label>
<label><input type="radio" name="v-{id}" value="not-entailed"><span>Not ensured</span></label>
<label><input type="radio" name="v-{id}" value="unsure"><span>Unsure</span></label>
</div>
<div class="which"><div class="tag" style="margin-top:6px">Which requirements are not ensured?</div>{which}</div>
<textarea placeholder="Optional comment"></textarea>
</section>"""


def title_of(item: dict) -> str:
    if item.get("number"):
        return f"Step {item['number']} of {STEPS_TOTAL}: {item['step']}"
    return item["step"][0].upper() + item["step"][1:]


def card(item: dict, num: int, n: int) -> str:
    groups = "".join(f'<div class="src">{E(g["from"])}:</div><ul>'
                     + "".join(f"<li>{E(c)}</li>" for c in g["conditions"]) + "</ul>"
                     for g in item["guarantee_sources"]) or "<ul><li>(none)</li></ul>"
    return CARD.format(id=item["id"], num=num, n=n, title=E(title_of(item)), guarantees=groups,
                       requires="".join(f"<li>{E(r)}</li>" for r in item["requires"]),
                       which="".join(f'<label><input type="checkbox" value="{E(r)}"> {E(r)}</label>'
                                     for r in item["requires"]))


def main() -> str:
    with open(os.path.join(RESULTS, "c5_items.json"), encoding="utf-8") as fh:
        items = json.load(fh)
    n = len(items)
    blocks, num = [], 0
    for r in sorted({i["round"] for i in items}):
        cards = []
        for it in [i for i in items if i["round"] == r]:
            num += 1
            cards.append(card(it, num, n))
        intro = ("One card per step, in workflow order."
                 if r == 1 else
                 "The same steps again, in workflow order, with somewhat different guarantees or requirements. "
                 "Judge each card on its own.")
        blocks.append(ROUND.format(title=f"3. Round {r} of 2", intro=intro, cards="\n".join(cards)))
    definitions = "".join(f"<dt>{E(t)}</dt><dd>{E(d)}</dd>" for t, d in DEFINITIONS)
    overview = OVERVIEW.split("\n", 1)[1] if "\n" in OVERVIEW else OVERVIEW
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(PAGE.format(n=n, diagram=DIAGRAM, overview=E(overview), definitions=definitions,
                             rounds="\n".join(blocks), ids=json.dumps([i["id"] for i in items])))
    return OUT


if __name__ == "__main__":
    print("written", main())
