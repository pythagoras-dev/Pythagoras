# Pythagoras Portal Architecture

Portals are the central architectural concept in Pythagoras. This document describes their design, hierarchy, lifecycle, and how they relate to function wrappers and persistent storage.

## The Portal Concept

A portal is a persistent gateway connecting your local code to the Pythagoras distributed environment. It acts as the "operating system" for Pythagoras functions — managing storage, execution context, logging, and scheduling. Just as a process depends on an OS for I/O and resource management, a Pythagoras function depends on a portal for all interactions with the persistent world outside the current execution session.

Portals solve three problems:

1. **Persistence**: Connecting ephemeral runtime state to durable storage that survives restarts and spans machines.
2. **Context**: Providing a shared execution environment (configuration, logging, caching) without global variables.
3. **Coordination**: Managing distributed execution queues and worker processes in swarming scenarios.

---

## Portal Class Hierarchy

Each portal class extends the previous one with exactly one coherent concern. The hierarchy is strict — no class skips a level.

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

**Usage guidance**: Most users should work with `SwarmingPortal` (via `get_portal()`) and the `@pure` decorator. Lower-level portal types are primarily useful for testing, debugging, or building custom execution models.

---

## Function Wrapper Hierarchy

Each portal type has a corresponding function wrapper class. The wrapper hierarchy mirrors the portal hierarchy:

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

| Scenario | Recommended Portal | Decorator |
|---|---|---|
| Quick exploration, development | Default portal (implicit via `get_portal()`) | `@pure` |
| Single-machine persistent caching | `PureCodePortal` with local `FileDirDict` | `@pure` |
| Multi-machine distributed execution | `SwarmingPortal` with S3-backed `root_dict` | `@pure` + `.swarm()` |
| Execution logging and debugging | `LoggingCodePortal` | `@logging` |
| Testing function autonomy | `AutonomousCodePortal` | `@autonomous` |
| Unit testing portals | `_PortalTester` context manager | Any |
