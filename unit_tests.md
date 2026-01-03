# Pythagoras Testing Guide: Semantics over Mechanics

This document defines how we write and organize tests for Pythagoras.
We use `pytest`. Our priority is to test semantics (the externally
observable behavior and contract) rather than mechanics (incidental
implementation details).

Unit tests serve two purposes:
1) verify that the current version behaves according to the documented
   contract / intent; and
2) act as a regression safety net so that incorrect future changes are
   unlikely to go unnoticed. When behavior changes intentionally, tests
   should force an explicit decision to update either the implementation,
   the tests, or the documented contract.


## Essentials Cheat Sheet

```yaml
# Quick Reference for Humans & LLMs

commands:
  install_dev: "uv pip install -e '.[dev]' --system"
  run_tests: "pytest -q"
  with_coverage: "coverage run -m pytest && coverage html"

naming_conventions:
  test_files: "test_*.py (mirror features/use-cases)"
  test_functions: "test_* (describe behavior, not implementation)"
  test_location: "tests/ subdirectories"

test_structure:
  style: "Plain functions (no test classes)"
  pattern: "Arrange–Act–Assert (AAA)"
  size: "12-25 lines ideal"
  focus: "One behavior per test"
  file_size: "Under 300-400 lines; split by feature if larger"

critical_dos:
  - "Test semantics and intent, not mechanics"
  - "Test observable behavior and contracts, not internals"
  - "Use plain assert statements (pytest style)"
  - "Prefer parametrization over duplicated tests"
  - "Use PortalTester blocks when testing portals"
  - "Use tmp_path for filesystem operations"
  - "Seed randomness locally for reproducibility"
  - "Keep tests deterministic and independent"

critical_donts:
  - "Don't reimplement algorithm logic in tests"
  - "Don't assert internal temporary values"
  - "Don't over-specify exact error text"
  - "Don't depend on dict/set ordering"
  - "Don't create test classes"
  - "Don't mock internal functions (fake boundaries instead)"
  - "Don't touch network or external services"

fixtures_and_data:
  prefer: "Simple setup in test body"
  factories: "Use data builders for complex inputs"
  cleanup: "Automatic via tmp_path and fixtures"
  isolation: "No shared state between tests"
```

## How to run tests locally
- Install dev dependencies (we use `uv` for speed, `pip` works too):
  - `uv pip install -e ".[dev]" --system`
  - (or `pip install -e ".[dev]"`)
- Run tests: `pytest -q`
- Optional coverage using `coverage` (HTML report in `htmlcov/`):
  - `coverage run -m pytest`
  - `coverage html` (open `htmlcov/index.html`)

## Core Principles
- Test Contract Semantics and Intent, Not Internal Mechanics
- Assert on observable behavior and contracts:
  - Inputs → outputs, state transitions, side effects, and emitted
    errors/exceptions.
  - Documented invariants (e.g., idempotency, ordering guarantees,
    stability) should be asserted.
- Avoid coupling tests to implementation details:
  - Don't reimplement the function's algorithm inside the test.
  - Don't assert internal temporary values, private attribute layouts,
    or exact call graphs unless part of the public contract.
  - Prefer assertions on result structure/meaning over exact strings
    or byte-for-byte snapshots. If text is part of the contract,
    assert structure and key substrings rather than entire messages.
- Prefer properties to single examples when suitable:
  - For example, round-trips (encode→decode→equal), monotonicity,
    associativity, or invariants across inputs.
- Test the public API; only test internals when necessary to pin down
  behavior that lacks a stable outer surface.
- Make illegal states unrepresentable in tests: construct inputs with
  realistic shapes, not arbitrary mocks.
- Always make sure tests are logically sound and semantically correct.

## Layout and Naming
- All tests live in `tests/` and its subdirectories.
- Test files start with `test_` and mirror features or use-cases.
- Keep files focused and small. Aim for under 300-400 lines per test
  file; if a file grows beyond this, split it by feature or
  sub-component. It's okay to create a separate file targeting a
  tricky branch.
- Create plain test functions. Do not create test classes.
- Test function names are `test_*` and describe the behavior under
  test. Prefer one focused behavior per test.
- Add a short docstring for non-obvious tests to state the intent and
  contract being exercised.
- Test helpers can live in the same module if local; if widely reused,
  extract to `tests/utils.py` or a fixture module.
- Prefer installed imports (e.g., `from Pythagoras ...`) over relative
  imports.

## Test Style
- Use plain `assert` statements (pytest style). Keep Arrange–Act–Assert
  (or Given–When–Then) ordering clear.
- Keep tests deterministic and independent. Avoid shared global state.
- Include negative tests with `pytest.raises` for error contracts
  (types, messages if they are part of the contract).
- Avoid fragile assertions:
  - Don't over-specify exact error text if only the error type matters.
  - Don't depend on dict/set ordering unless the API guarantees it.
  - Don't assert timestamps or random values exactly; assert
    ranges/relations.
- Prefer parametrization over duplicating near-identical tests.
- Avoid redundant/overlapping tests that cover the same behavior in
  the same way.

### Using `match` with `pytest.raises`
The `match` parameter in `pytest.raises` should be used judiciously:

**When to use `match`:**
- ✅ Good: When the error message is part of the public contract
  ```python
  # API promises to mention the field name in validation errors
  pytest.raises(ValueError, match="user_id")
  ```
- ✅ Good: When verifying that an error refers to a specific input/field
  ```python
  # Ensure the error message identifies the problematic parameter
  pytest.raises(TypeError, match="expected.*str.*got.*int")
  ```

**When to omit `match`:**
- ✅ Good: When only the exception type matters
  ```python
  # We only care that it raises ValueError, not the exact message
  with pytest.raises(ValueError):
      validate_input(None)
  ```
- ✅ Good: When testing platform/version-dependent internal errors
  ```python
  # Low-level errors vary by Python version and platform
  with pytest.raises(ValueError):
      "\0".encode("utf-8")  # Message wording is implementation detail
  ```

**Anti-patterns to avoid:**
- ❌ Fragile: Mechanical use of `match` on internal/low-level errors
  ```python
  # BAD: "embedded null character" wording varies by Python version
  pytest.raises(ValueError, match="embedded null character")
  ```
- ❌ Fragile: Cargo-cult addition of `match` when message is incidental
  ```python
  # BAD: Creates brittleness across platforms/versions for no benefit
  pytest.raises(OSError, match="File not found")
  ```

**Guideline:** Only use `match` when the error message content is part
of your API's documented contract or when you need to distinguish
between different error cases of the same type. Python's internal error
messages often vary by version, platform, and implementation—avoid
coupling tests to these incidental details.

## Fixtures, Test Data, and Doubles
- Prefer simple, explicit setup in the test body; use fixtures when it
  reduces duplication without hiding intent.
- Keep fixtures small and local in scope. Avoid complex, highly-coupled
  fixture graphs.
- Put testing code inside "with PortalTester" blocks when testing
  portals and/or portal-aware objects.
- Use data builders/factories for test inputs when they improve clarity.
  Keep defaults realistic.
- Use `tmp_path` for filesystem interactions. Clean-up should be
  automatic.
- Use fakes/stubs at system boundaries (I/O, network, clock, randomness).
  Avoid mocking internal functions.
- Verify interactions (e.g., call counts) only when they are part of
  the contract; otherwise assert effects/results.

## Randomness, Time, and Concurrency
- If behavior depends on randomness, seed locally inside the test to
  make failures reproducible and assert on properties/ranges.
- For time-dependent code, inject/patch the clock at the boundary.
  Prefer logical assertions (ordering, deltas) over exact instants.
- For concurrent code, assert eventual invariants or outcomes. Avoid
  brittle sleeps; if needed, keep them minimal and bounded.

## Isolation and Granularity
- Tests must be self-contained. Do not persist state between tests.
- While testing portals or portal-aware objects, always use
  _PortalTester
- Patch environment and process-wide state using `monkeypatch` within
  the test scope; restore automatically via fixtures.
- Avoid touching the network or external services in unit tests. Use
  fakes or local doubles.
 
## Size and Focus
- The ideal size of a unit test is between 12 and 25 lines.
- Prefer clear, compact, precise, and concise tests over overly verbose
  ones.
- Avoid tiny tests that assert trivial behavior; prefer meaningful,
  contract-focused tests.
- For small tests, group related assertions in one test rather than
  splitting into many single-assert tests.

## Coverage Philosophy
- Use coverage to discover untested behavior/branches, not to force
  trivial or mechanical asserts.
- It's acceptable to exercise internal branches to stabilize observable
  behavior (e.g., serialization markers), but don't ossify incidental
  details.
- For non-serialization modules, cover typical inputs and meaningful
  edge/boundary cases.

## Performance
- Keep unit tests fast (<1s typical). Avoid unnecessary sleeps, large
  inputs, or heavy loops in unit tests.
- If a slower test is valuable, mark it accordingly (e.g.,
  `@pytest.mark.slow`) and keep it isolated.

## Adding New Tests
- Start from the behavior/contract/intent: what must hold true for
  callers?
- Add both positive and negative cases; include boundary values and
  representative real-world inputs.
- Prefer parametrized tests for input matrices.
- Mirror existing structure and naming. For a new branch/marker, a
  dedicated `test_..._branch.py` that explains intent is welcome.
- Keep tests clear and maintainable. If a reader can't tell what
  behavior is specified, add a docstring.

## LLM-Friendly Test Patterns

This section provides guidance for writing tests that remain stable and
maintainable when AI/LLM agents generate or modify code.

### Design for Stability Under AI Changes

**Use helper factories for test data:**
- Create reusable builder functions that generate test objects with
  sensible defaults.
- Example: `def make_user(name="test", age=25, **overrides): ...`
- Benefit: When AI agents modify data structures, only the factory
  needs updating, not every test.

**Prefer semantic assertions over brittle checks:**
- ✅ Good: `assert result.status == "success"` or
  `assert len(items) > 0`
- ❌ Fragile: `assert str(result) ==
  "Result(status='success', code=200, timestamp=1234567890)"`
- LLM agents often regenerate exact strings/reprs; semantic checks
  survive reformatting.

**Keep error-message checks tolerant:**
- ✅ Good: `assert "invalid input" in str(excinfo.value).lower()`
- ❌ Fragile: `assert str(excinfo.value) ==
  "Error: Invalid input provided at line 42"`
- AI-generated error messages may vary in wording; check for key
  content, not exact phrasing.
- **Note on `pytest.raises(match=...)`:** Apply the same tolerance
  principle described in "Using `match` with `pytest.raises`" above.
  Only use `match` when the error message is part of the public
  contract. Python's internal error messages vary by version and
  platform—avoid coupling tests to these implementation details. Omit
  `match` when only the exception type matters.

**Avoid brittle regular expressions:**
- If you must use regex for validation, make patterns flexible (e.g.,
  `\s+` instead of ` `, optional groups).
- Prefer substring checks or structural assertions when possible.

**Use property-based checks where applicable:**
- Assert invariants: `assert output == sorted(output)` (monotonicity)
- Assert relationships: `assert len(filtered) <= len(original)`
- These are more robust than hardcoded examples when AI refactors
  implementations.

### Token and Complexity Considerations

**Avoid excessively deep parametrization matrices:**
- Large `@pytest.mark.parametrize` lists with many combinations can
  bloat prompt context for AI code reviews.
- ✅ Good: 3-10 parameter sets covering key cases
- ❌ Problematic: 50+ combinations exhaustively testing every edge case
- Consider splitting into multiple focused tests or using `hypothesis`
  for property testing instead.

**Keep test function bodies concise:**
- The 12-25 line guideline helps AI agents parse and reason about test
  logic efficiently.
- Very long tests (>50 lines) reduce LLM comprehension and increase
  hallucination risk.

**Use descriptive variable names:**
- `expected_user_count` is better than `x` or `result1`.
- Clear names help LLMs understand test intent and generate accurate
  modifications.

**Add docstrings for complex test logic:**
- A 1-2 sentence docstring helps AI agents understand what
  contract/behavior is being tested.
- Example:
  ```python
  def test_cache_invalidation_after_update():
      """Verify that updating an entity clears its cache entry."""
  ```
- LLMs use docstrings as semantic anchors when modifying or extending
  tests.

## Code Style and Contributing
- Follow PEP 8 and use type hints where appropriate (see
  `contributing.md`).
- Use concise, intention-revealing names.
- Commit message prefix for test changes: `TST:` (see
  `contributing.md`).
