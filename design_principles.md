# Core Design Principles of Pythagoras

Pythagoras applies functional programming principles — specifically function purity — to planet-scale distributed computing in Python. Pure functions (deterministic, side-effect-free) are the ideal unit of computation: their results can be safely cached, reused, and distributed without coordination. Pythagoras extends classical in-process memoization to persistent, cross-machine result storage — **compute once, reuse forever**.

## 1. Pure functions and referential transparency

The foundation of Pythagoras is the functional programming concept of **purity**. A pure function satisfies three properties:

1. **Deterministic** — the same inputs always produce the same output.
2. **Side-effect-free** — the function produces no observable effects beyond its return value.
3. **Referentially transparent** — any call to the function can be replaced by its cached result without changing program behavior.

Referential transparency is what makes memoization correct: if `f(x=5)` returned `25` once, it will return `25` forever, so the cached result can substitute for the call. Every successful pure-function execution is permanently stored; future calls with the same inputs return the stored result instantly.

The `@pure` decorator is the programmer's declaration that a function satisfies this contract. Python cannot verify purity statically; purity is a semantic promise, not a machine-checked proof.

## 2. Content-addressable storage

All values, function code, and execution results are addressed by their content hash (SHA-256, encoded in base-32). Addresses combine a human-readable descriptor with a deterministic hash, forming types like `ValueAddr` and `PureFnExecutionResultAddr`. Content addressing enables deduplication, immutable result caches, and transparent distributed access — any machine with access to the same storage backend can retrieve any result. Content addressing works because pure functions operate on immutable inputs and produce immutable outputs — values with stable, deterministic hashes.

## 3. Portals as layered execution environments

A portal manages persistent storage, execution context, logging, and scheduling for Pythagoras functions. Users interact with a single portal type: `SwarmingPortal`. Internally, it is built from a hierarchy of 10 single-concern layers that exist to reduce cognitive load on maintainers, not as a menu of user choices. For the full hierarchy, lifecycle, and storage layout, see [`portal_architecture.md`](portal_architecture.md).

## 4. Autonomous functions for distribution

Functions decorated with `@pure` (and custom extension functions decorated with `@autonomous`) must be self-contained: all imports inside the function body, no references to external globals, no closures, no `yield`. AST-based validation at decoration time and runtime checks during execution enforce these constraints. Autonomy ensures that a function can be serialized, transferred, and executed on any machine without external dependencies. For the full contract — what's allowed, what's forbidden, and how source normalization works — see [`autonomy_model.md`](autonomy_model.md).

Autonomy and purity are **independent**: autonomy makes functions distributable; purity makes them memoizable. `@pure` requires both. See [`autonomy_model.md`](autonomy_model.md) for the full distinction and examples.

## 5. Keyword-only arguments for canonical addressing

All decorated functions accept only keyword arguments — no positional arguments, no default values. This ensures a single canonical representation for any function call, which is essential for deterministic content-addressing and cache-key generation. The canonical representation packs arguments into a sorted, hashable form used to construct `PureFnExecutionResultAddr`.

## 6. Simple user API, layered internals

The user-facing API is intentionally minimal:

- Decorate functions with `@pure` for persistent memoization and distributed execution.
- Write custom extension functions (requirements, result checks) with `@autonomous`.
- Create a `SwarmingPortal` (or accept the default at `~/.pythagoras/.default_portal`) for distributed execution.
- Call `.swarm()` for asynchronous execution; retrieve results via `ready()` / `get()`.

Everything else is internal infrastructure — intermediate layers that decompose a complex system into testable, single-concern building blocks for maintainers. See [`portal_architecture.md`](portal_architecture.md) for the full list.

## 7. Source-code-aware caching

Pure function results are keyed by: function identity + normalized source code hash + packed argument hash. Source code is normalized before hashing — comments and docstrings are stripped, formatting is standardized (PEP 8) — so that cosmetic changes don't invalidate caches. Changing the actual logic triggers re-execution for the new code version, while previously cached results for older versions are preserved.

## 8. Extension mechanism: requirements and result checks

Pre-execution requirements (e.g., `unused_cpu`, `unused_ram`, `installed_packages`) and post-execution result checks are themselves autonomous functions. Requirements can be passive (check a condition) or active (install a missing package). This makes validation composable, distributable, and testable. Requirements returning `NO_OBJECTIONS` allow execution to proceed; any other return value signals a problem.

## 9. Swarming: eventual-execution distributed computing

The `.swarm()` method on `PureFn` enqueues a function call for asynchronous execution by any available worker process. Callers receive a `PureFnExecutionResultAddr` immediately — a "future" that can be polled via `ready()` and resolved via `get()`. Guarantees: at-least-once eventual execution. No guarantees: timing, worker assignment, or single execution. Swarming is safe because of purity: duplicate executions are harmless (idempotent), and any worker produces the same result for the same inputs — referential transparency applied to distributed scheduling.

## 10. Storage-agnostic via persidict

All persistent state — values, execution results, execution requests, run history, crash logs — flows through `persidict`, which provides pluggable backends (`FileDirDict` for local filesystem, `BasicS3Dict` / `S3Dict` for cloud, `LocalDict` for testing). Pythagoras inherits persidict's distributed access, serialization, caching, and write-once semantics without coupling to a specific storage mechanism. Switching from local development to cloud-scale deployment requires only changing the portal's `root_dict`.

## 11. Trade-offs and limitations

These choices come with explicit trade-offs:

- **Single-thread portal enforcement**: Portals use `SingleThreadEnforcerMixin` and are not thread-safe. Concurrent access requires separate processes, not threads.
- **No real-time guarantees**: Swarming provides eventual execution, not latency-bounded execution.
- **Autonomy constraints**: Self-contained function requirements prohibit closures, global state, and external imports at module scope — limiting what decorated functions can express.
- **Eventual consistency**: In distributed scenarios with shared storage, results may appear with delay.
- **Source tracking scope**: Only changes to the decorated function's own source code (and its requirements/result checks) trigger re-execution — changes in dependencies or environment are not tracked automatically.
- **Research preview**: Pythagoras is in alpha status; APIs may change between versions.
