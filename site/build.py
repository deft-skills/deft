"""Build the DEFT website into docs/.

    python site/build.py [--out docs]

The output is committed under docs/ and served as is by GitHub Pages (branch main,
folder /docs), which also lets anonymous mirrors serve the same site.

Everything on the site comes from the repository: guides are the Markdown files of
guides/ (and the example's README), the catalogue is generated from the example library
in models/, and the binding tables of workflows are computed by the checker.
"""
from __future__ import annotations

import argparse
import copy
import html
import itertools
import json
import os
import posixpath
import re
import shutil
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from deft import __version__  # noqa: E402
from deft.check import check_library, is_executable, obligations  # noqa: E402
from deft.generate import (generate, mermaid, render_skill,  # noqa: E402
                           render_workflow)
from deft.loader import load_library  # noqa: E402
from deft.model import MANY, CompositeSkill  # noqa: E402
from deft.resolve import provenance_trail, resolve  # noqa: E402

E = html.escape
PAST = {"declares": "declared", "implements": "implemented", "overrides": "overridden", "extends": "extended"}
MARKED = "https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
FONTS = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
         "&family=JetBrains+Mono:wght@400;500&display=swap")

# Guides: (site page, source file in the repository, title in the navigation)
GUIDES = [
    ("guides/metamodel.html", "guides/metamodel.md", "The metamodel"),
    ("guides/writing-models.html", "guides/modelling-guide.md", "Writing models"),
    ("guides/validating-models.html", "guides/constraints.md", "Validating models"),
    ("guides/generating-skills.html", "guides/generation.md", "Generating skills"),
    ("guides/using-skills.html", "guides/using-skills.md", "Using generated skills"),
    ("guides/example.html", "examples/account-service/README.md", "Example: deliver a feature"),
    ("guides/cli.html", "guides/cli.md", "Command line"),
]
FAMILY_ORDER = ["requirements", "planning", "implementation", "verification", "support"]


# ------------------------------------------------------------------ context

class Site:
    def __init__(self, out: str):
        self.out = out
        with open(os.path.join(HERE, "site.yaml"), encoding="utf-8") as fh:
            self.cfg = yaml.safe_load(fh)
        self.lib = load_library(os.path.join(ROOT, "models"))
        self.raw = self._raw_models()
        self.families: dict[str, list[str]] = {}
        for s in self.lib.skills.values():
            self.families.setdefault(s.family, []).append(s.name)

    def _raw_models(self) -> dict:
        raw = {}
        for s in self.lib.skills.values():
            with open(os.path.join(self.lib.root, s.file), encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
            for d in doc.get("skills", []):
                raw[d["name"]] = yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=100)
        return raw

    def children(self, name):
        return sorted(n for n, s in self.lib.skills.items() if s.parent == name)

    def source_url(self, path: str) -> str:
        return self.cfg["source_url"].format(path=path)

    def workflows(self):
        return sorted(n for n, s in self.lib.skills.items() if isinstance(s, CompositeSkill))


# ------------------------------------------------------------------ layout

NAV_TOP = [("index.html", "Overview"), ("guides/metamodel.html", "Guides"), ("catalogue.html", "Catalogue"),
           ("about.html", "About")]


def rel(depth: int, path: str) -> str:
    return "../" * depth + path


def sidebar(site: Site, depth: int, current: str) -> str:
    def link(path, label, cls=""):
        active = " active" if path == current else ""
        return f'<a class="{cls}{active}" href="{rel(depth, path)}">{E(label)}</a>'
    parts = ["<h4>Get started</h4>", link("index.html", "Overview"), link("quickstart.html", "Quickstart"),
             "<h4>Guides</h4>"]
    parts += [link(p, t) for p, _, t in GUIDES]
    parts += ["<h4>Catalogue</h4>", link("catalogue.html", "All skills")]
    for fam in FAMILY_ORDER + sorted(set(site.families) - set(FAMILY_ORDER) - {"workflows"}):
        if fam in site.families:
            parts.append(f'<a class="sub" href="{rel(depth, "catalogue.html")}#{fam}">{E(fam.capitalize())}</a>')
    parts.append(link("types.html", "Artifact types"))
    parts.append("<h4>Workflows</h4>")
    parts += [link(f"workflows/{w}.html", w) for w in site.workflows()]
    parts += ["<h4>Project</h4>", link("about.html", "About DEFT")]
    return "\n".join(parts)


def page(site: Site, path: str, title: str, body: str, toc: bool = True) -> None:
    depth = path.count("/")
    section = path.split("/")[0]
    top = "".join(
        f'<a class="{"active" if p == path or (p.startswith(section + "/") and "/" in path) else ""}" '
        f'href="{rel(depth, p)}">{E(label)}</a>' for p, label in NAV_TOP)
    toc_html = ('<aside class="toc"><h5>On this page</h5><nav id="toc-links"></nav></aside>' if toc else
                '<aside class="toc"></aside>')
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} · DEFT</title>
<meta name="description" content="DEFT: a metamodel and toolset to specialize, compose, check and generate agent skills.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{rel(depth, 'static/style.css')}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%231a1a1a'/%3E%3Ctext x='16' y='22' font-family='monospace' font-size='15' text-anchor='middle' fill='white'%3Edf%3C/text%3E%3C/svg%3E">
</head>
<body>
<header class="topbar">
  <button class="iconbtn menubtn" id="menu" aria-label="Menu">☰</button>
  <a class="brand" href="{rel(depth, 'index.html')}"><span class="brand-mark">df</span>DEFT</a>
  <nav class="topnav">{top}</nav>
  <span class="spacer"></span>
  <a class="iconbtn" href="{E(site.cfg['repo_url'])}">Repository</a>
  <button class="iconbtn" id="theme" aria-label="Toggle theme">◐</button>
</header>
<div class="layout">
<nav class="sidebar">{sidebar(site, depth, path)}</nav>
<main><div class="content">
{body}
<footer>DEFT {E(__version__)} · GNU General Public License v3.0 · Reused third-party skills keep their original licences.</footer>
</div></main>
{toc_html}
</div>
<script src="{MARKED}"></script>
<script src="{MERMAID}"></script>
<script src="{rel(depth, 'static/app.js')}"></script>
</body>
</html>
"""
    dest = os.path.join(site.out, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)


def md_block(key: str, text: str) -> str:
    """A Markdown string rendered client-side; the JSON escape keeps </script> safe."""
    payload = json.dumps(text).replace("</", "<\\/")
    return (f'<script type="application/json" id="md-{key}">{payload}</script>'
            f'<div class="md" data-md="md-{key}"><pre>{E(text)}</pre></div>')


def badge(text: str, cls: str = "") -> str:
    return f'<span class="badge {cls}">{E(text)}</span>'


def mult(lower: int, upper: int) -> str:
    up = "*" if upper == MANY else str(upper)
    return f"[{lower}..{up}]" if str(lower) != up else f"[{lower}]"


def skill_link(depth: int, name: str) -> str:
    return f'<a href="{rel(depth, "skills/" + name + ".html")}">{E(name)}</a>'


def type_link(depth: int, name: str) -> str:
    return f'<a href="{rel(depth, "types.html")}#t-{name}"><code>{E(name)}</code></a>'


def kind_of(sk) -> str:
    if isinstance(sk, CompositeSkill):
        return "workflow"
    return "abstract" if sk.abstract else "concrete"


def origins(lib, name):
    """(origin, declaring skill) along the hierarchy, nearest first."""
    return [(o, s) for s in lib.skill_ancestors(name) for o in lib.skills[s].origin]


def origin_badges(lib, name) -> str:
    seen = []
    for o, _ in origins(lib, name):
        label = f"{o.mode.value} from {o.repo}"
        if label not in seen:
            seen.append(label)
    return "".join(badge(x) for x in seen)


# ------------------------------------------------------------------ guides

_LINK = re.compile(r"\]\(([^)\s]+)\)")


def rewrite_links(site: Site, text: str, source: str, depth: int) -> str:
    """Point links of a repository Markdown file to site pages or repository files."""
    pages = {src: p for p, src, _ in GUIDES}
    base = posixpath.dirname(source)

    def repl(m):
        target = m.group(1)
        if re.match(r"^(https?:|mailto:|#)", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(base, path)) if path else source
        if resolved in pages:
            url = rel(depth, pages[resolved]) + (f"#{anchor}" if anchor else "")
        elif resolved == "README.md":
            url = rel(depth, "index.html")
        else:
            url = site.source_url(resolved.rstrip("/"))
        return f"]({url})"
    return _LINK.sub(repl, text)


def page_guide(site: Site, path: str, source: str, title: str, index: int) -> None:
    with open(os.path.join(ROOT, source), encoding="utf-8") as fh:
        text = fh.read()
    depth = path.count("/")
    text = rewrite_links(site, text, source, depth)
    prev_next = []
    if index > 0:
        p, _, t = GUIDES[index - 1]
        prev_next.append(f'<a class="card" href="{rel(depth, p)}"><p>Previous</p><h3>{E(t)}</h3></a>')
    if index + 1 < len(GUIDES):
        p, _, t = GUIDES[index + 1]
        prev_next.append(f'<a class="card" href="{rel(depth, p)}"><p>Next</p><h3>{E(t)}</h3></a>')
    body = f"""<div class="eyebrow">Guides</div>
<div class="guide">{md_block('guide', text)}</div>
<p style="margin-top:24px"><a class="iconbtn" href="{E(site.source_url(source))}">View source of this page</a></p>
<div class="cards">{''.join(prev_next)}</div>"""
    page(site, path, title, body)


# ------------------------------------------------------------------ pages

def page_index(site: Site) -> None:
    lib = site.lib
    wf = lib.skills["deliver-feature"]
    body = f"""
<section class="hero">
  <div class="eyebrow">Metamodel · Checks · Generator · Catalogue</div>
  <h1>DEFT</h1>
  <p class="lead">Engineer agent skills as software. DEFT lets you specialize skills into families, compose them
  into typed workflows, check both before any agent runs, and generate plain <code>SKILL.md</code> files that
  follow the <a href="https://agentskills.io/specification">Agent Skills specification</a>.</p>
  <p><a class="iconbtn" href="quickstart.html">Quickstart</a> <a class="iconbtn" href="guides/metamodel.html">Read the guides</a>
  <a class="iconbtn" href="catalogue.html">Browse the catalogue</a></p>
</section>

<h2 id="why">Why</h2>
<p>Agent skills are folders of instructions that coding agents load on demand. The specification fixes a few
metadata fields and leaves skills unrelated, so libraries grow by copying: a shared procedure is pasted into every
variant, and pipelines are described in prose ("then use skill X"). Copies drift, and a pipeline that wires two
incompatible skills fails only while an agent runs it.</p>

<div class="cards">
  <a class="card" href="guides/metamodel.html#specialization"><div class="icon">⊑</div><h3>Specialization</h3>
    <p>Skill families. A parent holds the procedure every variant shares; variants fill its variation points or
    change its defaults, and DEFT records where every instruction comes from.</p></a>
  <a class="card" href="guides/metamodel.html#composition"><div class="icon">→</div><h3>Composition</h3>
    <p>Workflows whose steps exchange typed artifacts, invoke other skills, repair failures a bounded number of
    times, and declare pre- and postconditions.</p></a>
  <a class="card" href="guides/validating-models.html"><div class="icon">✓</div><h3>Checks</h3>
    <p>Hierarchies, bindings and data flow are validated before execution. A variant that accepts a narrower
    input is fine in its family and rejected where it is wired to an incompatible step.</p></a>
  <a class="card" href="guides/generating-skills.html"><div class="icon">▤</div><h3>Plain skills out</h3>
    <p>Every model generates standard skill folders, with inputs, outputs, conditions, provenance and the licences
    of reused material. Agents need nothing new.</p></a>
</div>

<h2 id="how">How it works</h2>
<ol class="steps">
  <li><h3>Model</h3><p>Describe artifact types, skill families and workflows in YAML.
  <a href="guides/writing-models.html">Writing models</a>.</p></li>
  <li><h3>Check</h3><p><code>deft check models</code> validates both hierarchies, every refinement, binding and edge.
  <a href="guides/validating-models.html">Validating models</a>.</p></li>
  <li><h3>Generate</h3><p><code>deft generate models --out skills</code> writes one folder per concrete skill and
  workflow. <a href="guides/generating-skills.html">Generating skills</a>.</p></li>
  <li><h3>Run</h3><p>Install the folders in any compatible agent and ask it to use a workflow.
  <a href="guides/using-skills.html">Using generated skills</a>.</p></li>
</ol>

<h2 id="library">The example library</h2>
<p>DEFT ships with a library that delivers a feature request with a spec-driven process, built on public skills
from Spec Kit, Superpowers and anthropics/skills: requirements in several notations, planning, test-driven
implementation, acceptance and performance tests, and bounded repair. Its main workflow,
<a href="workflows/deliver-feature.html"><code>deliver-feature</code></a>:</p>
<pre class="mermaid">{E(mermaid(lib, wf))}</pre>
<p>Try it with a coding agent in the <a href="guides/example.html">example</a>.</p>
"""
    page(site, "index.html", "Overview", body)


def page_quickstart(site: Site) -> None:
    body = f"""
<div class="eyebrow">Get started</div>
<h1>Quickstart</h1>
<p class="lead">Install DEFT, check the example library, and generate its skills.</p>
<h2 id="install">Install</h2>
<p>Requires Python 3.11 or later.</p>
<p>Get the repository from <a href="{E(site.cfg['repo_url'])}">{E(site.cfg['repo_url'])}</a>, then:</p>
<pre><code>cd deft
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -e ".[test]"</code></pre>
<h2 id="check">Check the example library</h2>
<pre><code>deft check models
# 14 types, 21 skills: 0 violation(s)</code></pre>
<p>Bind an incompatible variant in <code>models/workflows/deliver-feature.yaml</code>, for instance
<code>bind: ears</code> for the <code>functional</code> node, and check again:</p>
<pre><code>[C2] workflow deliver-feature: data edge functional.requirements -> acceptance.requirements:
     EARSRequirement (from ears) does not conform to UserStory (required by acceptance-gherkin)</code></pre>
<h2 id="generate">Generate and inspect skills</h2>
<pre><code>deft resolve models volere           # the SKILL.md an agent receives for 'volere'
deft generate models --out skills    # one folder per concrete skill and workflow
deft obligations models              # contracts to review in the workflows</code></pre>
<h2 id="next">Next</h2>
<div class="cards">
  <a class="card" href="guides/metamodel.html"><h3>The metamodel</h3><p>Specialization, composition, and why they are checked together.</p></a>
  <a class="card" href="guides/writing-models.html"><h3>Writing models</h3><p>Types, families, workflows, and reuse of third-party skills.</p></a>
  <a class="card" href="guides/example.html"><h3>Run the example</h3><p>Deliver a feature request with a coding agent and the generated skills.</p></a>
  <a class="card" href="catalogue.html"><h3>Browse the catalogue</h3><p>Every skill of the example library, resolved and generated.</p></a>
</div>
"""
    page(site, "quickstart.html", "Quickstart", body)


def readme_section(heading: str) -> str:
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def page_about(site: Site) -> None:
    ai = readme_section("Use of generative AI")
    ai = rewrite_links(site, ai, "README.md", 0)
    contrib = readme_section("Contributing")
    contrib = rewrite_links(site, contrib, "README.md", 0)
    body = f"""
<div class="eyebrow">Project</div>
<h1>About DEFT</h1>
<p class="lead">DEFT is an open metamodel and toolset for engineering agent skills, with an example library built
on public skills.</p>
<h2 id="contents">What the repository contains</h2>
<table>
<tr><th>Path</th><th>Contents</th></tr>
<tr><td><code>guides/</code></td><td>The guides published on this site.</td></tr>
<tr><td><code>docs/</code></td><td>This website, generated by <code>site/build.py</code>.</td></tr>
<tr><td><code>deft/</code></td><td>The <code>deft</code> tool: loader, resolution, checks, generator, diagrams, command line.</td></tr>
<tr><td><code>metamodel/</code></td><td>The metamodel in Ecore and OCL, and diagrams.</td></tr>
<tr><td><code>models/</code></td><td>The example library.</td></tr>
<tr><td><code>skills/</code></td><td>Skills generated from the example library.</td></tr>
<tr><td><code>examples/</code></td><td>A runnable example with a coding agent.</td></tr>
<tr><td><code>upstream/</code></td><td>Pinned third-party skills reused by the example library, with their licences.</td></tr>
<tr><td><code>experiments/</code></td><td>Scripts of the research evaluation of DEFT.</td></tr>
</table>
<h2 id="contribute">Contributing</h2>
{md_block('contrib', contrib)}
<h2 id="ai">Use of generative AI</h2>
{md_block('ai', ai)}
<h2 id="licence">Licence</h2>
<p>DEFT is released under the GNU General Public License v3.0. Third-party material under <code>upstream/</code>
keeps its MIT or Apache-2.0 licence; generated skills that reuse it ship the original licence text next to their
<code>SKILL.md</code>.</p>
<p>Repository: <a href="{E(site.cfg['repo_url'])}">{E(site.cfg['repo_url'])}</a></p>
"""
    page(site, "about.html", "About", body)


def page_types(site: Site) -> None:
    lib = site.lib

    def tree(name, depth=0):
        t = lib.types[name]
        cls = "abs" if t.abstract else ""
        line = (f'<div style="padding-left:{depth * 18}px"><a class="{cls}" href="#t-{name}">{E(name)}</a>'
                f'{" (abstract)" if t.abstract else ""}</div>')
        kids = sorted(n for n, x in lib.types.items() if x.parent == name)
        return line + "".join(tree(k, depth + 1) for k in kids)
    roots = sorted(n for n, t in lib.types.items() if not t.parent)
    blocks = []
    for n, t in lib.types.items():
        props = "".join(f"<tr><td><code>{E(p.name)}</code></td><td>{mult(p.lower, p.upper)}</td>"
                        f"<td>{E(p.description or (', '.join(p.values)))}</td></tr>" for p in t.properties)
        users = sorted({s.name for s in lib.skills.values() for p in s.parameters if p.type == n})
        blocks.append(f"""<h3 id="t-{n}">{E(n)} {badge('abstract', 'abstract') if t.abstract else ''}</h3>
<p>{E(t.description)}{' Specializes ' + type_link(0, t.parent) + '.' if t.parent else ''}</p>
{'<table><tr><th>Property</th><th>Mult.</th><th>Notes</th></tr>' + props + '</table>' if props else ''}
<p class="badges">{''.join(f'<a class="badge" href="skills/{u}.html">{E(u)}</a>' for u in users)}</p>""")
    body = f"""
<div class="eyebrow">Catalogue</div>
<h1>Artifact types</h1>
<p class="lead">The artifacts that skills of the example library exchange. Parameters refer to these types, and data
edges are checked against their hierarchy.</p>
<h2 id="hierarchy">Hierarchy</h2>
<div class="tree">{''.join(tree(r) for r in roots)}</div>
<h2 id="types">Types</h2>
{''.join(blocks)}
"""
    page(site, "types.html", "Artifact types", body)


def page_catalogue(site: Site) -> None:
    lib = site.lib
    sections = []
    for fam in FAMILY_ORDER + ["workflows"] + sorted(set(site.families) - set(FAMILY_ORDER) - {"workflows"}):
        names = site.families.get(fam)
        if not names:
            continue
        cards = []
        for n in names:
            sk = lib.skills[n]
            k = kind_of(sk)
            path = f"workflows/{n}.html" if k == "workflow" else f"skills/{n}.html"
            lineage = " › ".join(reversed(lib.skill_ancestors(n)))
            cards.append(f"""<a class="card" href="{path}" data-skill="{E((n + ' ' + sk.description).lower())}" data-kind="{k}">
<h3>{E(n)}</h3><p>{E(sk.description)}</p>
<div class="badges">{badge(k, 'abstract' if k == 'abstract' else '')}{origin_badges(lib, n)}</div>
{f'<p style="margin-top:8px;font-size:.8rem;color:var(--fg-faint)">{E(lineage)}</p>' if sk.parent else ''}</a>""")
        sections.append(f'<h2 id="{fam}">{E(fam.capitalize())}</h2><div class="cards">{"".join(cards)}</div>')
    body = f"""
<div class="eyebrow">Catalogue</div>
<h1>Skills</h1>
<p class="lead">The example library: {len(lib.skills)} skills in {len(site.families)} families. Concrete skills and
workflows are generated as <code>SKILL.md</code> folders; abstract skills exist only in the models and reach agents
through their specializations.</p>
<input class="search" id="search" type="search" placeholder="Filter skills" aria-label="Filter skills">
<div class="filters">
  <button class="chip active" data-kind="all">All</button>
  <button class="chip" data-kind="concrete">Concrete</button>
  <button class="chip" data-kind="abstract">Abstract</button>
  <button class="chip" data-kind="workflow">Workflows</button>
</div>
{''.join(sections)}
"""
    page(site, "catalogue.html", "Catalogue", body)


def _signature_table(site: Site, name: str, depth: int) -> str:
    rows = []
    for p in site.lib.effective_params(name).values():
        declared = next(s for s in site.lib.skill_ancestors(name) if site.lib.skills[s].param(p.name))
        rows.append(f"<tr><td>{p.direction.value}</td><td><code>{E(p.name)}</code></td>"
                    f"<td>{type_link(depth, p.type)} {mult(p.lower, p.upper)}</td>"
                    f"<td>{skill_link(depth, declared) if declared != name else 'here'}</td></tr>")
    return ("<table><tr><th>Dir.</th><th>Parameter</th><th>Type</th><th>Declared by</th></tr>"
            + "".join(rows) + "</table>") if rows else "<p>No parameters.</p>"


def _conditions(site: Site, name: str) -> str:
    pre, post = site.lib.effective_conditions(name)

    def li(xs):
        return "<ul>" + "".join(f"<li>{E(x)}</li>" for x in xs) + "</ul>" if xs else "<p>None.</p>"
    return f"<h3>Preconditions</h3>{li(pre)}<h3>Postconditions</h3>{li(post)}"


def _tabs(tabs) -> str:
    btns = "".join(f'<button class="tab{" active" if i == 0 else ""}" data-panel="p-{k}">{E(label)}</button>'
                   for i, (k, label, _) in enumerate(tabs))
    panels = "".join(f'<div class="tabpanel{" active" if i == 0 else ""}" id="p-{k}">{c}</div>'
                     for i, (k, _, c) in enumerate(tabs))
    return f'<div data-tabs><div class="tabs">{btns}</div></div>{panels}'


def page_skill(site: Site, name: str) -> None:
    lib, depth = site.lib, 1
    sk = lib.skills[name]
    r = resolve(lib, name)
    chain = " › ".join(skill_link(depth, s) if s != name else f"<strong>{E(s)}</strong>" for s in r.chain)
    kids = site.children(name)
    blocks = []
    for s in r.sections:
        prov = provenance_trail(s, lambda x: skill_link(depth, x))
        content = s.content.strip()
        if content:
            body = f'<div class="section-body">{md_block(f"sec-{s.name}", content)}</div>'
        else:
            msg = "Implemented by each concrete descendant." if not s.filled else "Empty."
            body = f'<div class="section-body empty">{msg}</div>'
        blocks.append(f"""<div class="section-block"><div class="section-head">{badge(s.kind.value, s.kind.value)}
<strong>{E(s.title or s.name)}</strong><span class="prov">{prov}</span></div>{body}</div>""")
    tabs = [("sections", "Resolved sections", "".join(blocks))]
    if not sk.abstract:
        text = render_skill(lib, name, provenance=False)
        fm_end = text.find("\n---", 3)
        front, md = text[:fm_end + 4], text[fm_end + 4:].lstrip()
        tabs.append(("generated", "Generated SKILL.md", f"""
<p><a class="iconbtn" href="../skills-dist/{name}/SKILL.md" download>Download SKILL.md</a>
<button class="iconbtn" data-copy="raw-{name}">Copy</button></p>
<pre><code>{E(front)}</code></pre><div class="section-body">{md_block('gen', md)}</div>
<pre id="raw-{name}" hidden>{E(text)}</pre>"""))
    tabs.append(("model", "Model", f"<p>From <code>models/{E(sk.file)}</code>.</p>"
                                   f"<pre><code>{E(site.raw.get(name, ''))}</code></pre>"))
    used_in = sorted({w.name for w in lib.skills.values() if isinstance(w, CompositeSkill)
                      for n in w.skill_nodes() if name in (n.role, n.bind)})
    origin_rows = "".join(
        f"<tr><td>{E(o.repo)}</td><td><code>{E(o.path)}</code></td><td><code>{E(o.commit[:7])}</code></td>"
        f"<td>{E(o.license)}</td><td>{E(o.mode.value)}</td><td>{skill_link(depth, by) if by != name else 'here'}</td></tr>"
        for o, by in origins(lib, name))
    origin_html = ("<h2 id=\"origin\">Origin</h2><table><tr><th>Repository</th><th>Path</th><th>Commit</th>"
                   "<th>Licence</th><th>Mode</th><th>Declared by</th></tr>" + origin_rows + "</table>"
                   if origin_rows else "")
    body = f"""
<div class="eyebrow">{E(sk.family.capitalize())}</div>
<h1>{E(name)}</h1>
<p class="lead">{E(sk.description)}</p>
<div class="badges">{badge(kind_of(sk), 'abstract' if sk.abstract else '')}{origin_badges(lib, name)}</div>
<dl class="kv">
<dt>Lineage</dt><dd>{chain}</dd>
<dt>Specializations</dt><dd>{', '.join(skill_link(depth, k) for k in kids) or 'none'}</dd>
<dt>Used in</dt><dd>{', '.join(f'<a href="../workflows/{w}.html">{E(w)}</a>' for w in used_in) or 'no workflow'}</dd>
</dl>
<h2 id="signature">Signature</h2>
{_signature_table(site, name, depth)}
{_conditions(site, name)}
<h2 id="instructions">Instructions</h2>
{_tabs(tabs)}
{origin_html}
"""
    page(site, f"skills/{name}.html", name, body)


def binding_space(lib, name: str):
    """Every binding of the roles with several concrete specializations, checked."""
    wf = lib.skills[name]

    def candidates(role):
        return sorted(n for n, s in lib.skills.items()
                      if not s.abstract and not isinstance(s, CompositeSkill) and lib.conforms_skill(n, role))
    points = [(n.name, candidates(n.role)) for n in wf.skill_nodes() if len(candidates(n.role)) > 1]
    rows = []
    for combo in itertools.product(*[c for _, c in points]):
        trial = copy.deepcopy(lib)
        for (nid, _), skill in zip(points, combo):
            trial.skills[name].node(nid).bind = skill
        found = [v for v in check_library(trial) if v.element == f"workflow {name}"]
        rows.append((combo, found))
    return points, rows


def page_workflow(site: Site, name: str) -> None:
    lib, depth = site.lib, 1
    wf = lib.skills[name]
    nodes = "".join(
        f"<tr><td><code>{E(n.name)}</code></td><td>{skill_link(depth, n.role)}</td>"
        f"<td>{skill_link(depth, n.bind) if n.bind else '(role)'}</td></tr>" for n in wf.skill_nodes())
    obs = "".join(
        f"<tr><td><code>{E(o.target)}</code></td><td>{E(', '.join(o.sources))}</td>"
        f"<td><ul>{''.join('<li>' + E(c) + '</li>' for c in o.pre)}</ul></td></tr>" for o in obligations(lib, wf))
    points, rows = binding_space(lib, name)
    head = "".join(f"<th>{E(p)}</th>" for p, _ in points)
    trs = "".join(
        "<tr>" + "".join(f"<td><code>{E(v)}</code></td>" for v in combo)
        + "<td>" + (badge("valid", "ok") if not found else badge(found[0].code, "bad")
                    + f'<div style="font-size:.8rem;color:var(--fg-faint)">{E(found[0].message)}</div>') + "</td></tr>"
        for combo, found in rows)
    valid = sum(1 for _, f in rows if not f)
    text = render_workflow(lib, wf, provenance=False)
    fm_end = text.find("\n---", 3)
    md = text[fm_end + 4:].lstrip()
    body = f"""
<div class="eyebrow">Workflow</div>
<h1>{E(name)}</h1>
<p class="lead">{E(wf.description)}</p>
<div class="badges">{badge('executable' if is_executable(lib, wf) else 'template', 'ok')}</div>
<h2 id="graph">Graph</h2>
<p>Solid edges carry artifacts, labelled with the type the receiving step requires; dashed edges invoke a skill or
repair after a failure.</p>
<pre class="mermaid">{E(mermaid(lib, wf))}</pre>
<h2 id="nodes">Steps and bindings</h2>
<table><tr><th>Step</th><th>Role</th><th>Bound to</th></tr>{nodes}</table>
<h2 id="bindings">Alternative bindings</h2>
<p>Steps whose role has several concrete specializations can be bound differently. The checker decides which
combinations are valid: {valid} of {len(rows)} here. Invalid ones wire a variant to a step that cannot accept what
it produces.</p>
<table><tr>{head}<th>Check</th></tr>{trs}</table>
<h2 id="contracts">Contracts to review</h2>
<p>For every step, the postconditions of the steps before it, and the guards that lead to it, must guarantee its
preconditions. These are natural-language conditions: review them (<code>deft obligations models --workflow
{E(name)}</code>).</p>
<table><tr><th>Step</th><th>After</th><th>Preconditions to guarantee</th></tr>{obs}</table>
<h2 id="generated">Generated SKILL.md</h2>
<p><a class="iconbtn" href="../skills-dist/{name}/SKILL.md" download>Download SKILL.md</a></p>
<div class="section-body">{md_block('wf', md)}</div>
"""
    page(site, f"workflows/{name}.html", name, body)


# ------------------------------------------------------------------ main

def build(out: str) -> None:
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    site = Site(out)
    shutil.copytree(os.path.join(HERE, "static"), os.path.join(out, "static"))
    generate(site.lib, os.path.join(out, "skills-dist"))
    page_index(site)
    page_quickstart(site)
    for i, (path, source, title) in enumerate(GUIDES):
        page_guide(site, path, source, title, i)
    page_catalogue(site)
    page_types(site)
    page_about(site)
    for name, sk in site.lib.skills.items():
        if isinstance(sk, CompositeSkill):
            page_workflow(site, name)
        else:
            page_skill(site, name)
    with open(os.path.join(out, ".nojekyll"), "w") as fh:
        fh.write("")
    print(f"site written to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "docs"))
    build(ap.parse_args().out)
