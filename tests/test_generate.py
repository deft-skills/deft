"""Generated skills conform to the Agent Skills specification."""
import os

from skills_ref.validator import validate

from deft.generate import generate, topological_steps
from deft.loader import load_library

ROOT = os.path.join(os.path.dirname(__file__), "..", "models")


def test_generated_skills_pass_reference_validator(tmp_path):
    lib = load_library(ROOT)
    names = generate(lib, str(tmp_path))
    concrete = [n for n, s in lib.skills.items() if not s.abstract]
    assert sorted(names) == sorted(concrete)
    for n in names:
        assert validate(tmp_path / n) == [], n


def test_upstream_licences_travel_with_adapted_skills(tmp_path):
    lib = load_library(ROOT)
    generate(lib, str(tmp_path))
    assert (tmp_path / "volere" / "LICENSE-spec-kit.txt").exists()
    assert (tmp_path / "test-driven-development" / "LICENSE-superpowers.txt").exists()
    assert (tmp_path / "acceptance-playwright" / "scripts" / "with_server.py").exists()
    assert not list((tmp_path / "quantify-quality").glob("LICENSE-*"))


def test_workflow_order_respects_dependencies():
    lib = load_library(ROOT)
    order = topological_steps(lib.skills["deliver-feature"])
    assert order.index("plan") > order.index("functional")
    assert order.index("implement") > order.index("plan")
    assert order.index("verdict") > order.index("performance")
    assert order.index("debug") > order.index("verdict")


def test_abstract_sections_never_reach_agents(tmp_path):
    lib = load_library(ROOT)
    generate(lib, str(tmp_path), provenance=False)
    text = (tmp_path / "user-stories" / "SKILL.md").read_text(encoding="utf-8")
    assert "As a <role>" in text and "<!-- deft" not in text


def test_optional_fields_are_inherited(tmp_path):
    from deft.generate import render_skill
    lib = load_library(ROOT)
    lib.skills["specify-requirements"].compatibility = "Needs git."
    lib.skills["specify-requirements"].allowed_tools = "Read Write"
    lib.skills["volere"].license = "MIT"
    text = render_skill(lib, "volere")
    assert "license: MIT" in text and "compatibility: Needs git." in text
    assert "allowed-tools: Read Write" in text
