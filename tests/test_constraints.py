"""One positive and at least one negative case per constraint."""
import copy
import os

import pytest

from deft.check import check_library, obligations
from deft.loader import ModelError, library_from_dict, load_library
from deft.resolve import resolve

ROOT = os.path.join(os.path.dirname(__file__), "..", "models")

TYPES = {"types": [
    {"name": "Req", "abstract": True},
    {"name": "Story", "parent": "Req"},
    {"name": "Ears", "parent": "Req"},
    {"name": "Code"},
]}


def base_skills():
    return {"skills": [
        {"name": "spec", "abstract": True, "description": "d",
         "parameters": [{"name": "out", "direction": "out", "type": "Req"}],
         "sections": [{"name": "f", "kind": "final", "content": "F"},
                      {"name": "a", "kind": "abstract"},
                      {"name": "h", "kind": "default", "content": "H"}]},
        {"name": "stories", "parent": "spec", "description": "d",
         "parameters": [{"name": "out", "direction": "out", "type": "Story"}],
         "refinements": [{"kind": "implements", "target": "a", "content": "A"},
                         {"kind": "extends", "target": "h", "content": "H2"}]},
        {"name": "ears", "parent": "spec", "description": "d",
         "parameters": [{"name": "out", "direction": "out", "type": "Ears"}],
         "refinements": [{"kind": "implements", "target": "a", "content": "A"},
                         {"kind": "overrides", "target": "h", "content": "H3"}]},
        {"name": "test", "description": "d",
         "parameters": [{"name": "reqs", "direction": "in", "type": "Story"},
                        {"name": "code", "direction": "out", "type": "Code"}]},
    ]}


def workflow():
    return {"skills": [{
        "name": "wf", "composite": True, "description": "d",
        "parameters": [{"name": "code", "direction": "out", "type": "Code"}],
        "nodes": [{"name": "s", "role": "spec", "bind": "stories"},
                  {"name": "t", "role": "test"}],
        "data": [{"from": "s.out", "to": "t.reqs"}, {"from": "t.code", "to": "self.code"}],
    }]}


def lib_of(*docs):
    return library_from_dict([(f"doc{i}.yaml", d) for i, d in enumerate(docs)])


def codes(lib):
    return sorted({v.code for v in check_library(lib)})


def test_valid_toy_library():
    assert codes(lib_of(TYPES, base_skills(), workflow())) == []


def test_running_example_is_valid():
    lib = load_library(ROOT)
    assert check_library(lib) == []
    assert {"deliver-feature", "deliver-feature-iso"} <= set(lib.skills)


def test_resolution_and_provenance():
    lib = lib_of(TYPES, base_skills())
    r = resolve(lib, "stories")
    assert [s.name for s in r.sections] == ["f", "a", "h"]
    assert r.section("a").content == "A"
    assert r.section("h").content == "H\n\nH2"
    assert [c.action for c in r.section("h").sources] == ["declares", "extends"]
    assert resolve(lib, "ears").section("h").content == "H3"


def test_placeholders():
    s = base_skills()
    s["skills"][0]["sections"][0]["content"] = "Before {{name}} ({{meta.phase}})"
    s["skills"][1]["metadata"] = {"phase": "specify"}
    assert resolve(lib_of(TYPES, s), "stories").section("f").content == "Before stories (specify)"


def test_s1_cycle_and_multiple_parents():
    s = base_skills()
    s["skills"][0]["parent"] = "stories"
    assert "T1" in codes(lib_of(TYPES, s))
    s = base_skills()
    s["skills"][1]["parent"] = ["spec", "test"]
    with pytest.raises(ModelError):
        lib_of(TYPES, s)


def test_s2_missing_implementation():
    s = base_skills()
    s["skills"][1]["refinements"] = s["skills"][1]["refinements"][1:]
    assert codes(lib_of(TYPES, s)) == ["T2"]


@pytest.mark.parametrize("ref", [
    {"kind": "overrides", "target": "f", "content": "x"},   # final section
    {"kind": "implements", "target": "h", "content": "x"},  # default, not abstract
    {"kind": "extends", "target": "a", "content": "x"},     # abstract, not default
    {"kind": "overrides", "target": "zz", "content": "x"},  # undeclared
])
def test_s3_bad_refinements(ref):
    s = base_skills()
    s["skills"][1]["refinements"].append(ref)
    assert "T3" in codes(lib_of(TYPES, s))


def test_s3_redeclaration():
    s = base_skills()
    s["skills"][1]["sections"] = [{"name": "f", "kind": "final", "content": "again"}]
    assert "T3" in codes(lib_of(TYPES, s))


def test_s4_widening_and_direction():
    s = base_skills()
    s["skills"][1]["parameters"][0]["type"] = "Code"
    assert "T4" in codes(lib_of(TYPES, s))
    s = base_skills()
    s["skills"][1]["parameters"][0]["direction"] = "in"
    assert "T4" in codes(lib_of(TYPES, s))


def _typed(child_lower, child_upper):
    return {"types": [
        {"name": "Req", "properties": [{"name": "criteria", "lower": 1, "upper": "*"},
                                       {"name": "metric", "lower": 0, "upper": 1}]},
        {"name": "Story", "parent": "Req",
         "properties": [{"name": "criteria", "lower": child_lower, "upper": child_upper}]},
    ]}


def test_s4_property_narrowing_is_allowed():
    assert codes(lib_of(_typed(2, "*"))) == []
    assert codes(lib_of(_typed(1, 3))) == []


@pytest.mark.parametrize("lower,upper", [(0, "*"), (0, 1)])
def test_s4_property_widening(lower, upper):
    assert codes(lib_of(_typed(lower, upper))) == ["T4"]


def test_generated_artifact_fields_use_nearest_declaration(tmp_path):
    from deft.generate import _artifact_lines
    lines = _artifact_lines(lib_of(_typed(2, "*")), "Story")
    assert any("`criteria` (2 or more)" in line for line in lines)


def test_wf_resource_folder_matches_kind():
    s = base_skills()
    s["skills"][3]["resources"] = [{"path": "references/run.py", "kind": "script", "source": "x"}]
    assert codes(lib_of(TYPES, s)) == ["WF"]
    s["skills"][3]["resources"] = [{"path": "scripts/run.py", "kind": "script", "source": "x"}]
    assert codes(lib_of(TYPES, s)) == []


UPSTREAM_TDD = "../upstream/superpowers/skills/test-driven-development/SKILL.md"
ORIGIN = {"repo": "obra/superpowers", "path": "skills/test-driven-development/SKILL.md",
          "commit": "8ca22db", "license": "MIT"}


def _imported(origin_mode, with_source):
    section = {"name": "procedure", "kind": "final"}
    section.update({"source": UPSTREAM_TDD} if with_source else {"content": "own text"})
    skill = {"name": "tdd", "description": "d", "sections": [section]}
    if origin_mode:
        skill["origin"] = [dict(ORIGIN, mode=origin_mode)]
    return library_from_dict([("t.yaml", TYPES), ("s.yaml", {"skills": [skill]})], root=ROOT)


def test_wf_imported_origin_and_source_go_together():
    assert codes(_imported("imported", True)) == []
    assert codes(_imported(None, False)) == []           # authored from scratch
    assert codes(_imported("adapted", False)) == []
    assert codes(_imported("imported", False)) == ["WF"]  # claims import, copies nothing
    assert codes(_imported("adapted", True)) == ["WF"]    # reads upstream, not declared
    assert codes(_imported(None, True)) == ["WF"]


def test_origin_mode_is_an_enumeration():
    with pytest.raises(ValueError):
        _imported("created", False)


def test_c1_abstract_or_unrelated_binding():
    w = workflow()
    w["skills"][0]["nodes"][0]["bind"] = "spec"
    assert "C1" in codes(lib_of(TYPES, base_skills(), w))
    w = workflow()
    w["skills"][0]["nodes"][0]["bind"] = "test"
    assert "C1" in codes(lib_of(TYPES, base_skills(), w))


def test_c2_cross_dimension_type_error():
    """Binding EARS upstream of a test skill that requires user stories."""
    w = workflow()
    w["skills"][0]["nodes"][0]["bind"] = "ears"
    assert codes(lib_of(TYPES, base_skills(), w)) == ["C2"]


def test_c2_unbound_template_is_checked_on_roles():
    w = workflow()
    del w["skills"][0]["nodes"][0]["bind"]
    # role 'spec' produces Req, which does not conform to Story
    assert "C2" in codes(lib_of(TYPES, base_skills(), w))


def test_c3_missing_input():
    w = workflow()
    w["skills"][0]["data"] = w["skills"][0]["data"][1:]
    assert codes(lib_of(TYPES, base_skills(), w)) == ["C3"]


def test_c4_cycle_bound_and_invocation():
    w = workflow()
    w["skills"][0]["control"] = [{"kind": "sequence", "from": "t", "to": "s"}]
    assert "C4" in codes(lib_of(TYPES, base_skills(), w))
    w = workflow()
    w["skills"][0]["control"] = [{"kind": "repair", "from": "t", "to": "s"}]
    assert "C4" in codes(lib_of(TYPES, base_skills(), w))
    w = workflow()
    w["skills"][0]["control"] = [{"kind": "repair", "from": "t", "to": "s", "bound": 2}]
    assert codes(lib_of(TYPES, base_skills(), w)) == []


def test_running_example_seeded_faults():
    lib = load_library(ROOT)
    wf = lib.skills["deliver-feature"]
    bad = copy.deepcopy(lib)
    bad.skills["deliver-feature"].node("functional").bind = "ears"
    assert [v.code for v in check_library(bad)] == ["C2"]
    bad = copy.deepcopy(lib)
    bad.skills["deliver-feature"].node("quality").bind = "iso25010"
    assert [v.code for v in check_library(bad)] == ["C2"]
    assert obligations(lib, wf)


def test_composite_of_iso_variant_uses_adapter():
    lib = load_library(ROOT)
    nodes = {n.name for n in lib.skills["deliver-feature-iso"].nodes}
    assert "quantify" in nodes


def _grandchild(*refinements):
    """A specialization of 'stories' with the given refinements."""
    return {"skills": [{"name": "stories-lite", "parent": "stories", "description": "d",
                        "refinements": list(refinements)}]}


def test_refined_sections_become_default():
    lib = lib_of(TYPES, base_skills())
    r = resolve(lib, "stories")
    assert [(s.name, s.kind.value, s.declared.value) for s in r.sections] == [
        ("f", "final", "final"), ("a", "default", "abstract"), ("h", "default", "default")]
    # an implemented section can be overridden further down
    assert codes(lib_of(TYPES, base_skills(), _grandchild(
        {"kind": "overrides", "target": "a", "content": "A2"}))) == []
    # but no longer implemented again
    assert "T3" in codes(lib_of(TYPES, base_skills(), _grandchild(
        {"kind": "implements", "target": "a", "content": "A2"})))


def test_sealed_sections_admit_no_refinement():
    s = base_skills()
    s["skills"][1]["refinements"][0]["final"] = True
    lib = lib_of(TYPES, s)
    assert resolve(lib, "stories").section("a").kind.value == "final"
    assert codes(lib) == []
    assert "T3" in codes(lib_of(TYPES, s, _grandchild(
        {"kind": "overrides", "target": "a", "content": "A2"})))


def test_inout_parameters_are_inputs_and_outputs():
    types = {"types": TYPES["types"] + [{"name": "Plan"}]}
    skills = base_skills()
    skills["skills"].append({"name": "review", "description": "d",
                             "parameters": [{"name": "plan", "direction": "inout", "type": "Plan"}]})
    wf = {"skills": [{
        "name": "wf2", "composite": True, "description": "d",
        "parameters": [{"name": "plan", "direction": "inout", "type": "Plan"}],
        "nodes": [{"name": "r", "role": "review"}],
        "data": [{"from": "self.plan", "to": "r.plan"}, {"from": "r.plan", "to": "self.plan"}],
    }]}
    assert codes(lib_of(types, skills, wf)) == []
    wf["skills"][0]["data"] = wf["skills"][0]["data"][1:]
    assert codes(lib_of(types, skills, wf)) == ["C3"]  # the inout input is not fed


def test_skills_specialize_skills_of_their_kind():
    w = workflow()
    w["skills"][0]["parent"] = "spec"
    assert "WF" in codes(lib_of(TYPES, base_skills(), w))


def test_composite_skills_have_no_sections():
    w = workflow()
    w["skills"][0]["sections"] = [{"name": "x", "content": "y"}]
    with pytest.raises(ModelError):
        lib_of(TYPES, base_skills(), w)
