# Pythagoras Portal Architecture

Portals are the central architectural concept in Pythagoras. This document describes their design, hierarchy, lifecycle, and how they relate to function wrappers and persistent storage. It is written primarily for maintainers and contributors — users typically interact only with `SwarmingPortal` and the `@pure` decorator.

## The Portal Concept

A portal is a persistent gateway connecting your local code to the Pythagoras distributed environment. It acts as the "operating system" for Pythagoras functions — managing storage, execution context, logging, and scheduling. Just as a process depends on an OS for I/O and resource management, a Pythagoras function depends on a portal for all interactions with the persistent world outside the current execution session.

Portals solve three problems:

1. **Persistence**: Connecting ephemeral runtime state to durable storage that survives restarts and spans machines.
2. **Context**: Providing a shared execution environment (configuration, logging, caching) without global variables.
3. **Coordination**: Managing distributed execution queues and worker processes in swarming scenarios.

---

## Portal Class Hierarchy

Each portal class extends the previous one with exactly one coherent concern. The hierarchy is strict — no class skips a level. Users interact only with `SwarmingPortal`; the intermediate classes exist to keep each layer small and focused for maintainers.

| Portal Class | Module | What It Adds |
|---|---|---|
| `BasicPortal` | `_210_basic_portals` | Lifecycle, registration, portal stack, context manager protocol, `describe()` |
| `DataPortal` | `_220_data_portals` | Content-addressable storage (`HashAddr`, `ValueAddr`), persistent value store via `persidict` |
| `TunablePortal` | `_230_tunable_portals` | Per-portal and per-object settings management |
| `OrdinaryCodePortal` | `_310_ordinary_code_portals` | `OrdinaryFn` management, function registration, normalized source code |
| `LoggingCodePortal` | `_320_logging_code_portals` | Execution logging: `_run_history`, `_crash_history`, `_event_history`; stdout/stderr capture |
| `SafeCodePortal` | `_330_safe_code_portals` | Safer execution defaults (foundation for future sandboxing via RestrictedPython) |
| `AutonomousCodePortal` | `_340_autonomous_code_portals` | AST-based autonomy validation for self-contained functions |
| `GuardedCodePortal` | `_350_guarded_code_portals` | Pre-execution requirements and post-execution result checks |
| `PureCodePortal` | `_360_pure_code_portals` | Persistent result caching via `_execution_results` (append-only) and `_execution_requests` (mutable queue) |
| `SwarmingPortal` | `_410_swarming_portals` | Asynchronous distributed execution, worker process management |

---

## Function Wrapper Hierarchy

Each portal type from `OrdinaryCodePortal` onward has a corresponding function wrapper class. The wrapper hierarchy mirrors the portal hierarchy. Users interact with `PureFn` (via `@pure`) and `AutonomousFn` (via `@autonomous`, for custom extension functions); the intermediate wrappers are internal.

| Wrapper Class | Decorator | Portal Type | Key Feature |
|---|---|---|---|
| `OrdinaryFn` | `@ordinary` | `OrdinaryCodePortal` | Source normalization, keyword-only enforcement, no defaults |
| `LoggingFn` | `@logging` | `LoggingCodePortal` | Execution attempt/result logging, stdout/stderr capture |
| `SafeFn` | `@safe` | `SafeCodePortal` | Safer argument handling (foundation for sandboxing) |
| `AutonomousFn` | `@autonomous` | `AutonomousCodePortal` | AST-validated self-containment: all imports inside body, no globals, no closures |
| `GuardedFn` | `@guarded` | `GuardedCodePortal` | Runs `requirements` before and `result_checks` after execution |
| `PureFn` | `@pure` | `PureCodePortal` | Deterministic result caching; provides `.swarm()`, `.run()`, `.get_address()`, `.fix_kwargs()` |

There is no `SwarmingFn` — swarming is activated by calling `.swarm()` on a `PureFn` within a `SwarmingPortal` context. This keeps the function wrapper hierarchy focused on function-level concerns while swarming remains a portal-level capability.

---

## Portal Lifecycle

### Creation and Registration

When a portal is instantiated, it registers itself in a global `_PORTAL_REGISTRY`. The registry tracks:

- **Known portals**: All portal instances created in the current process.
- **Active portal stack**: A stack of portals entered via context managers, with re-entrancy support.
- **Current portal**: The innermost portal on the active stack.

### Context Managers

Portals are used as context managers:

```python
portal = SwarmingPortal("/path/to/storage")

with portal:
    # portal is now "current" — decorators and functions use it implicitly
    @pure()
    def compute(x: float) -> float:
        return x * x

    result = compute(x=5.0)
# portal is no longer current
```

Entering a portal pushes it onto the active stack. Exiting pops it. Portals can be nested — the innermost is always "current."

### Default Portal

If no portal is active and a function requires one, Pythagoras creates a default `SwarmingPortal` at `~/.pythagoras/.default_portal`. This provides a zero-configuration starting point, though explicit portal creation is recommended for production use.

### Portal States

A portal instance can be in one of these states:

- **Known**: Instantiated and registered, but not on the active stack.
- **Active**: On the active stack (entered via `with` statement). May appear multiple times (re-entrant).
- **Current**: The innermost portal on the active stack. This is the portal that functions use when no specific portal is specified.

---

## Portal-Aware Objects

`PortalAwareObject` is the base class for objects that require portal access. All function wrappers (`OrdinaryFn` through `PureFn`) inherit from it. A portal-aware object can be:

- **Linked to a specific portal**: The object always uses that portal, regardless of which portal is current.
- **Dynamically bound**: The object uses the current portal from the stack at call time.

When a portal-aware object is created, it registers itself with its linked portal (or the current portal). The portal tracks all its linked objects, enabling introspection via `portal.get_linked_objects()` and `portal.count_linked_objects()`.

---

## Portal Storage Layout

Every portal has a `_root_dict` — a `PersiDict` instance that serves as the root of its persistent storage. Higher-level portals create subdictionaries for specific concerns:

| Subdictionary | Portal Level | Purpose |
|---|---|---|
| `values` | `DataPortal` | Content-addressable value store (`ValueAddr`) |
| `run_history` | `LoggingCodePortal` | Per-function execution attempt logs |
| `crash_history` | `LoggingCodePortal` | Exception/crash records |
| `event_history` | `LoggingCodePortal` | Application-level event logs |
| `execution_results` | `PureCodePortal` | Append-only cache of pure function results (wrapped in `WriteOnceDict`) |
| `execution_requests` | `PureCodePortal` | Mutable queue of pending swarming requests |

All subdictionaries are instances of the same `PersiDict` backend type as the root, inheriting its storage location and serialization format. The `execution_results` subdictionary uses `WriteOnceDict` wrapping and append-only semantics — once a result is stored, it is never overwritten.

---

## Pure Function Execution Flow

### Synchronous execution (`fn(x=5)`)

```
@pure decorator applied
  │
  ▼
PureFn wrapper created ──linked to──▶ PureCodePortal
  │
  ▼
fn(x=5) called
  │
  ├─▶ Build PureFnCallSignature(fn_identity + code_hash + packed_kwargs)
  │
  ├─▶ Build PureFnExecutionResultAddr from signature
  │
  ├─▶ Check execution_results[addr]
  │     ├── HIT  → return cached result (no execution)
  │     └── MISS ↓
  │
  ├─▶ Run requirements (autonomous functions)
  │     └── Any objection? → raise / abort
  │
  ├─▶ Execute function body
  │
  ├─▶ Run result_checks (autonomous functions)
  │
  ├─▶ Store result in execution_results[addr]  (WriteOnceDict)
  │
  └─▶ Return result
```

### Asynchronous execution (`fn.swarm(x=5)`)

```
fn.swarm(x=5)
  ├─▶ Build addr (same as synchronous flow)
  ├─▶ Store request in execution_requests[addr]
  └─▶ Return addr immediately

Worker process (later):
  ├─▶ Pick request from execution_requests
  ├─▶ Execute fn(x=5) through the synchronous flow above
  └─▶ Remove request from execution_requests
```

Callers poll the result via `ready(addr)` and retrieve it via `get(addr)`.

---

## Module Numbering Convention

Source modules under `src/pythagoras/` use a numbered prefix convention:

```
_110_supporting_utilities
_210_basic_portals
_220_data_portals
_230_tunable_portals
_310_ordinary_code_portals
_320_logging_code_portals
_330_safe_code_portals
_340_autonomous_code_portals
_350_guarded_code_portals
_360_pure_code_portals
_410_swarming_portals
_800_top_level_API
```

The numbering enforces a strict dependency rule: **a module may only import from modules with lower numbers.** This eliminates circular dependencies by construction and makes the dependency graph immediately visible in the file listing. The hundreds digit groups related concerns:

- **1xx**: Foundational utilities (no Pythagoras-specific dependencies)
- **2xx**: Portal foundation and data storage
- **3xx**: Function wrapping, from basic to pure
- **4xx**: Distributed execution
- **8xx**: User-facing convenience API

Test directories under `tests/` mirror this numbering, making it straightforward to locate tests for any module.

---

## Choosing the Right Portal

### For users

Users should use `SwarmingPortal` (or accept the default) with `@pure`. This is the only combination designed for end-user code:

| Scenario | Setup | API |
|---|---|---|
| Quick exploration | Default portal (implicit) | `@pure` + direct calls |
| Single-machine persistent caching | `SwarmingPortal("/local/path")` | `@pure` + direct calls |
| Multi-machine distributed execution | `SwarmingPortal` with S3-backed `root_dict` | `@pure` + `.swarm()` / `ready()` / `get()` |

### For maintainers and contributors

Lower-level portal types are useful during development, debugging, and testing:

| Scenario | Portal | Decorator |
|---|---|---|
| Testing function registration | `OrdinaryCodePortal` | `@ordinary` |
| Debugging execution logs | `LoggingCodePortal` | `@logging` |
| Validating autonomy constraints | `AutonomousCodePortal` | `@autonomous` |
| Testing requirements/checks | `GuardedCodePortal` | `@guarded` |
| Testing caching without swarming | `PureCodePortal` | `@pure` |
| Unit testing portals in isolation | `_PortalTester` context manager | Any |

---

## Design Rationale

Key architectural decisions and why they were made.

### Why a deep class hierarchy that users never see

The 10-class portal chain decomposes a complex system into single-concern layers. Each class adds exactly one capability (storage, logging, autonomy validation, caching, swarming). Users see only `SwarmingPortal` and `@pure` — the internal layers exist to make the codebase navigable for contributors. A new contributor working on logging only needs to understand `LoggingCodePortal` and `LoggingFn`, not the entire system.

### Why context managers, not global singletons

Multiple portals can coexist within one process — for example, one backed by local files for development, another by S3 for production. Nesting via context managers enables scoped configuration without hidden global state. The stack model also supports re-entrancy: entering the same portal twice increments a counter rather than failing.

### Why 1:1 portal-to-wrapper mirroring

Each function wrapper type (`OrdinaryFn`, …, `PureFn`) needs exactly the storage and capabilities provided by its corresponding portal level. A `PureFn` requires `execution_results` storage (from `PureCodePortal`), autonomy validation (from `AutonomousCodePortal`), logging (from `LoggingCodePortal`), etc. Decoupling the hierarchies would create invalid combinations (e.g., a `PureFn` linked to a `BasicPortal` that has no result cache) and require runtime compatibility checks that the type system handles for free.

### Why single-thread enforcement

Portals manage mutable persistent state (execution queues, result caches) and registry membership. Making them thread-safe would require pervasive locking, adding complexity incompatible with the distributed execution model. Pythagoras achieves parallelism through multiple processes (swarming), not threads — each process has its own portal instance.

### Why WriteOnceDict for execution_results

Results of pure functions are immutable by definition — same inputs always produce the same output. `WriteOnceDict` wrapping prevents accidental overwrites and enables `persidict`'s append-only caching optimization, which skips cache validation for keys that are already present.

### Why no SwarmingFn

Swarming is a deployment topology concern (how many workers, where they run), not a function-level concern (what the function computes). Keeping swarming at the portal level avoids a combinatorial explosion of wrapper types and keeps the function hierarchy focused on computation semantics. A `PureFn` decorated with `@pure` works identically whether called directly or via `.swarm()` — only the execution scheduling differs.
