# Pythagoras Testing Guide: Semantics over Mechanics

This document defines how we write and organize tests for Pythagoras. We use `pytest`.
Our priority is to test semantics (the externally observable behavior and contract)
rather than mechanics (incidental implementation details).

Unit tests serve two purposes:
1) verify that the current version behaves according to the documented contract / intent; and
2) act as a regression safety net so that incorrect future changes are unlikely to go unnoticed. 
   When behavior changes intentionally, tests should force an explicit decision to update either the implementation, 
   the tests, or the documented contract.

## How to run tests locally
- Install dev dependencies (we use `uv` for speed, but `pip` works too):
  - `uv pip install -e ".[dev]" --system` (or `pip install -e ".[dev]"`)
- Run tests: `pytest -q`
- Optional coverage using `coverage` (HTML report in `htmlcov/`):
  - `coverage run -m pytest`
  - `coverage html` (open `htmlcov/index.html`)

## Core Principles
- Test Contract Semantics and Intent, Not Internal Mechanics
- Assert on observable behavior and contracts:
  - Inputs → outputs, state transitions, side effects, and emitted errors/exceptions.
  - Documented invariants (e.g., idempotency, ordering guarantees, stability) should be asserted.
- Avoid coupling tests to implementation details:
  - Don’t reimplement the function’s algorithm inside the test.
  - Don’t assert internal temporary values, private attribute layouts, or exact call graphs unless part of the public contract.
  - Prefer assertions on result structure/meaning over exact strings or byte-for-byte snapshots. If text is part of the contract, assert structure and key substrings rather than entire messages.
- Prefer properties to single examples when suitable:
  - For example, round-trips (encode→decode→equal), monotonicity, associativity, or invariants across inputs.
- Test the public API; only test internals when necessary to pin down behavior that lacks a stable outer surface.
- Make illegal states unrepresentable in tests: construct inputs with realistic shapes, not arbitrary mocks.
- Always make sure tests are logically sound and semantically correct.

## Layout and Naming
- All tests live in `tests/` and its subdirectories.
- Test files start with `test_` and mirror features or use-cases.
- Keep files focused and small. It’s okay to create a separate file targeting a tricky branch.
- Create plain test functions. Do not create test classes.
- Test function names are `test_*` and describe the behavior under test. Prefer one focused behavior per test.
- Add a short docstring for non-obvious tests to state the intent and contract being exercised.
- Test helpers can live in the same module if local; if widely reused, extract to `tests/utils.py` or a fixture module.
- Prefer installed imports (e.g., `from Pythagoras ...`) over relative imports.

## Test Style
- Use plain `assert` statements (pytest style). Keep Arrange–Act–Assert (or Given–When–Then) ordering clear.
- Keep tests deterministic and independent. Avoid shared global state.
- Include negative tests with `pytest.raises` for error contracts (types, messages if they are part of the contract).
- Avoid fragile assertions:
  - Don’t over-specify exact error text if only the error type matters.
  - Don’t depend on dict/set ordering unless the API guarantees it.
  - Don’t assert timestamps or random values exactly; assert ranges/relations.
- Prefer parametrization over duplicating near-identical tests.
- Avoid redundant/overlapping tests that cover the same behavior in the same way.

## Fixtures, Test Data, and Doubles
- Prefer simple, explicit setup in the test body; use fixtures when it reduces duplication without hiding intent.
- Keep fixtures small and local in scope. Avoid complex, highly-coupled fixture graphs.
- Put testing code inside "with PortalTester" blocks when testing portals and/or portal-aware objects.
- Use data builders/factories for test inputs when they improve clarity. Keep defaults realistic.
- Use `tmp_path` for filesystem interactions. Clean-up should be automatic.
- Use fakes/stubs at system boundaries (I/O, network, clock, randomness). Avoid mocking internal functions.
- Verify interactions (e.g., call counts) only when they are part of the contract; otherwise assert effects/results.

## Randomness, Time, and Concurrency
- If behavior depends on randomness, seed locally inside the test to make failures reproducible and assert on properties/ranges.
- For time-dependent code, inject/patch the clock at the boundary. Prefer logical assertions (ordering, deltas) over exact instants.
- For concurrent code, assert eventual invariants or outcomes. Avoid brittle sleeps; if needed, keep them minimal and bounded.

## Isolation and Granularity
- Tests must be self-contained. Do not persist state between tests.
- While testing portals or portal-aware objects, always use _PortalTester
- Patch environment and process-wide state using `monkeypatch` within the test scope; restore automatically via fixtures.
- Avoid touching the network or external services in unit tests. Use fakes or local doubles.
 
## Size and Focus
- The ideal size of a unit test is between 12 and 25 lines. 
- Prefer clear, compact, precise, and concise tests over overly verbose ones.
- Avoid tiny tests that assert trivial behavior; prefer meaningful, contract-focused tests.
- For small tests, group related assertions in one test rather than splitting into many single-assert tests.

## Coverage Philosophy
- Use coverage to discover untested behavior/branches, not to force trivial or mechanical asserts.
- It’s acceptable to exercise internal branches to stabilize observable behavior (e.g., serialization markers), but don’t ossify incidental details.
- For non-serialization modules, cover typical inputs and meaningful edge/boundary cases.

## Performance
- Keep unit tests fast (<1s typical). Avoid unnecessary sleeps, large inputs, or heavy loops in unit tests.
- If a slower test is valuable, mark it accordingly (e.g., `@pytest.mark.slow`) and keep it isolated.

## Adding New Tests
- Start from the behavior/contract/intent: what must hold true for callers?
- Add both positive and negative cases; include boundary values and representative real-world inputs.
- Prefer parametrized tests for input matrices.
- Mirror existing structure and naming. For a new branch/marker, a dedicated `test_..._branch.py` that explains intent is welcome.
- Keep tests clear and maintainable. If a reader can’t tell what behavior is specified, add a docstring.

## Code Style and Contributing
- Follow PEP 8 and use type hints where appropriate (see `contributing.md`).
- Use concise, intention-revealing names.
- Commit message prefix for test changes: `TST:` (see `contributing.md`).
