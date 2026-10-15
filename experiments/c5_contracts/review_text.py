"""The instructions shared by human reviewers and LLM judges of C5 obligations."""

DEFINITIONS = [
    ("Requirement of a step",
     "A condition that the skill performing the step declares it needs before it starts "
     "(its precondition). For the last card, the requirements are what the whole workflow "
     "promises when it ends (its postconditions)."),
    ("Guarantee",
     "A condition known to hold when the step starts. It comes from one of three sources: "
     "a step that finished before it promised it (that step's postcondition); the workflow "
     "reached the step only under that condition (the outcome of a decision); or the whole "
     "workflow assumes it from the start (the workflow's precondition)."),
    ("Ensured",
     "Every requirement of the step follows from its guarantees, read with common sense. "
     "Do not assume anything about the system or the agent that the guarantees do not say."),
    ("Not ensured",
     "At least one requirement does not follow from the guarantees. Name every such requirement."),
]

OVERVIEW = """The workflow delivers a feature request in an existing system. Each numbered step is carried out with one skill:
1. specify the functional requirements as user stories, and
2. specify the quality requirements as Volere snow cards (both start from the feature request);
3. plan the implementation as test-first tasks (from the requirements of steps 1 and 2);
4. implement the plan task by task, test-first (from the plan);
5. write and run acceptance tests for the user stories, and
6. write and run load tests for the quality requirements (both on the code of step 4);
then a decision: if every test report passes, the workflow ends; if some report fails,
7. diagnose the failing tests, and go back to step 4 with the diagnosis (at most three times)."""


def definitions_text() -> str:
    return "\n".join(f"- {term}: {text}" for term, text in DEFINITIONS)
