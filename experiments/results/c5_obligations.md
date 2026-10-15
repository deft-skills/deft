# C5 obligations

For every node `n`, the postconditions of its predecessors and the guards that reach it must jointly entail the preconditions of `n`.

## deliver-feature

### functional (from self)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.

Must entail:
- The feature request is not empty.

### quality (from self)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.

Must entail:
- The feature request is not empty.

### plan (from functional, quality)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every requirement has a unique id and names its source.
- Every requirement is testable and unambiguous.
- No open clarification markers remain.
- Every functional requirement describes observable behaviour of the system.
- Every user story has at least one acceptance criterion in Given/When/Then form.
- Every quality requirement names one ISO/IEC 25010 characteristic.
- Every Volere requirement has a fit criterion with a metric, a threshold and a scale.

Must entail:
- Every requirement has a unique id and is testable.

### implement (from plan, debug)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- The plan has at least one task.
- Every requirement id is covered by at least one task.
- Every task names its files, its interfaces and the test that proves it.
- The diagnosis names a root cause supported by evidence, not a symptom.

Must entail:
- The plan has at least one task and every task names its test.

### acceptance (from functional, implement)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every requirement has a unique id and names its source.
- Every requirement is testable and unambiguous.
- No open clarification markers remain.
- Every functional requirement describes observable behaviour of the system.
- Every user story has at least one acceptance criterion in Given/When/Then form.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.

Must entail:
- The code builds and its existing tests pass.

### performance (from quality, implement)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every requirement has a unique id and names its source.
- Every requirement is testable and unambiguous.
- No open clarification markers remain.
- Every quality requirement names one ISO/IEC 25010 characteristic.
- Every Volere requirement has a fit criterion with a metric, a threshold and a scale.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.

Must entail:
- The code builds and its existing tests pass.
- An environment that matches production in configuration is available.

### debug (from acceptance, performance, implement, verdict)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every input requirement is covered by at least one test.
- The report states a verdict and the command that reproduces it.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.
- some report has verdict fail

Must entail:
- At least one report has verdict fail.

### self (from implement, acceptance, performance, verdict)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.
- Every input requirement is covered by at least one test.
- The report states a verdict and the command that reproduces it.
- every report has verdict pass

Must entail:
- Every requirement is covered by at least one passing test.
- The code is committed on a feature branch.

## deliver-feature-iso

### functional (from self)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.

Must entail:
- The feature request is not empty.

### quality (from self)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.

Must entail:
- The feature request is not empty.

### plan (from functional, quantify)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every requirement has a unique id and names its source.
- Every requirement is testable and unambiguous.
- No open clarification markers remain.
- Every functional requirement describes observable behaviour of the system.
- Every user story has at least one acceptance criterion in Given/When/Then form.
- Every output requirement has a fit criterion with a metric, a threshold and a scale.
- Every output requirement keeps the id and source of its input requirement.

Must entail:
- Every requirement has a unique id and is testable.

### implement (from plan, debug)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- The plan has at least one task.
- Every requirement id is covered by at least one task.
- Every task names its files, its interfaces and the test that proves it.
- The diagnosis names a root cause supported by evidence, not a symptom.

Must entail:
- The plan has at least one task and every task names its test.

### acceptance (from functional, implement)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every requirement has a unique id and names its source.
- Every requirement is testable and unambiguous.
- No open clarification markers remain.
- Every functional requirement describes observable behaviour of the system.
- Every user story has at least one acceptance criterion in Given/When/Then form.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.

Must entail:
- The code builds and its existing tests pass.

### performance (from quantify, implement)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every output requirement has a fit criterion with a metric, a threshold and a scale.
- Every output requirement keeps the id and source of its input requirement.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.

Must entail:
- The code builds and its existing tests pass.
- An environment that matches production in configuration is available.

### debug (from acceptance, performance, implement, verdict)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every input requirement is covered by at least one test.
- The report states a verdict and the command that reproduces it.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.
- some report has verdict fail

Must entail:
- At least one report has verdict fail.

### self (from implement, acceptance, performance, verdict)

Guarantees:
- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.
- Every task is committed on a dedicated feature branch.
- The full test suite passes, including the tests that existed before.
- Every deviation from the plan is recorded as a ruling.
- Every input requirement is covered by at least one test.
- The report states a verdict and the command that reproduces it.
- every report has verdict pass

Must entail:
- Every requirement is covered by at least one passing test.
- The code is committed on a feature branch.

