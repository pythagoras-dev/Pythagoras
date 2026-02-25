# Pythagoras Vocabulary (Glossary)

This glossary defines the key terms used in the Pythagoras project and API.

## 1. Core Concepts

- **Pure Functions:** Deterministic, side-effect-free, referentially transparent functions — a concept from functional programming. `@pure` is the programmer's declaration of this contract. See [Principle 1](design_principles.md#1-pure-functions-and-referential-transparency).

- **Referential Transparency:** A pure function call can be replaced by its cached result without changing program behavior. This is what makes memoization correct.

- **Memoization:** Caching function results and returning the cached result for identical future calls. Safe only for pure functions. Pythagoras extends memoization to persistent, cross-machine storage.

- **Immutability:** Once stored, values and execution results are never modified. Enforced by `WriteOnceDict` and content-addressable storage.

- **Partial Application:** Fixing some arguments of a function to create a specialized version. Provided by `fix_kwargs()` on function wrappers — used in place of closures (forbidden by autonomy).

- **Compute Once, Reuse Forever:** Every successful pure-function result is permanently stored; identical future calls return the cached result. See [Principle 1](design_principles.md#1-pure-functions-and-referential-transparency).

- **Content-Addressable Storage (CAS):** A storage mechanism where data is retrieved based on its content (hash) rather than its location. Pythagoras uses CAS for code, arguments, and results.

- **Swarming:** An asynchronous execution model where pure-function calls are enqueued and may be executed later by any available worker. Guarantees at least once eventual execution but not ordering or single execution.

- **Serverless:** An execution model where the system dynamically manages the allocation of machine resources in the cloud / distributed environment. Pythagoras implements a serverless-like experience using shared storage to coordinate distributed workers.

## 2. Portals

- **Portal:** The execution environment for Pythagoras functions — manages storage, scheduling, logging, and security. Users interact only with `SwarmingPortal`. See [`portal_architecture.md`](portal_architecture.md).

### 2.1. Portal Classes

- **BasicPortal:** The foundational portal class that manages lifecycle and registration of portal-aware objects.

- **DataPortal:** Extends `BasicPortal` with persistent storage for inputs, outputs, and metadata using `persidict`.

- **TunablePortal:** Extends `DataPortal` with support for storing / retrieving settings that can be tuned per portal or per object.

- **OrdinaryCodePortal:** Extends `TunablePortal` to work with decorated ordinary functions.

- **LoggingCodePortal:** Extends `OrdinaryCodePortal` with application-level and function-level logging (events, crashes, frames), capturing stdout/stderr.

- **SafeCodePortal:** Extends `LoggingCodePortal` with safer defaults for argument handling and execution bookkeeping.

- **AutonomousCodePortal:** Extends `SafeCodePortal` with self-contained execution support and autonomous primitives.

- **GuardedCodePortal:** Extends `AutonomousCodePortal` with requirements and result checks around function execution (pre/post execution hooks).

- **PureCodePortal:** Extends `GuardedCodePortal` to support pure functions with deterministic caching keyed by code and arguments.

- **SwarmingPortal:** Extends `PureCodePortal` to provide asynchronous, distributed execution ("swarming") across processes or machines.

### 2.2. Portal-related Concepts

- **Known Portals:** The set of all portal objects that have been instantiated and registered in the system.

- **Active Portals:** A stack of portals that are currently in scope (e.g., entered via context managers).

- **Current Portal:** The portal at the top of the active portals stack. It is the target for operations when no specific portal is provided.

- **Default Portal:** A `SwarmingPortal` auto-created when no portal is active and a function requires one.

## 3. Functions & Execution

- **PortalAwareObject:** An object that requires access to a Portal to function. It may be permanently linked to a specific portal instance or dynamically use the currently active portal. Examples include all function wrappers (e.g., `PureFn`, `OrdinaryFn`).

- **Function Decorators:** A family of decorators that create portal-bound callable wrappers with progressively more features:
  - `ordinary`: Basic wrapper around a Python function.
  - `logging`: Adds execution logging and output capture (`LoggingCodePortal`).
  - `safe`: Safer execution defaults (`SafeCodePortal`).
  - `autonomous`: Enables autonomous scheduling (`AutonomousCodePortal`).
  - `guarded`: Adds requirements and result checks (`GuardedCodePortal`).
  - `pure`: Declares a function as pure (deterministic, side-effect free) with persistent result caching (`PureCodePortal`).

  *Note: There is no `swarming` decorator. Swarming capabilities are provided by `SwarmingPortal` and the `.swarm()` method on pure functions.*

- **Function Wrappers (OrdinaryFn / LoggingFn / SafeFn / AutonomousFn / GuardedFn / PureFn):** The classes created by the corresponding decorators. `PureFn` is the most feature-rich and is the typical user-facing class for deterministic computation.

- **Call Signature:** An immutable description of a specific function call (function identity plus normalized/packed keyword arguments) used for caching, addressing, and logging.

- **swarm():** A method on `PureFn` that queues an asynchronous execution request and returns an address for the future result.

- **Compute Node:** An entry representing a worker or process capable of executing queued requests within a `SwarmingPortal`.

- **Execution Requests:** The persistent queue of requests to execute a function call (used by swarming to distribute work).

- **Execution Results:** The persistent records storing outputs of function calls, typically under `execution_results` in `PureCodePortal`.

- **Extensions:** Functions used to enforce preconditions and postconditions around execution. Examples include:
  - `requirements`: Checks before running a function (e.g., resource availability).
  - `result_checks`: Checks after running a function.
  - `recursive_parameters`: A helper indicating which parameters are recursive in mutual recursion scenarios.

## 4. Data & Storage

### 4.1. PersiDicts

- **PersiDict:**  An abstract base class for persistent, key–value storage backed by systems like local disk, S3, or MemoryDB. It exposes a standard `MutableMapping` (dict-like) API, so Pythagoras can remain storage-agnostic. The implementation lives in the external `persidict` library, built as Pythagoras’s storage abstraction layer.

- **FileDirDict:** A concrete implementation of `PersiDict` that stores data in a local file system directory. Each key corresponds to a file path, and the value is the file content.

- **BasicS3Dict:** A concrete implementation of `PersiDict` that stores data in an AWS S3 bucket. It maps keys to S3 objects, enabling distributed access to shared state.

### 4.2. Addresses

- **HashAddr:** A base address type that represents a hash-keyed location in persistent storage.

- **ValueAddr:** An address type for values stored in persistent storage.

- **PureFnExecutionResultAddr:** An address that uniquely identifies cached results of a `PureFn` call based on function identity, code, and packed arguments.

## 5. API & Utilities

- **ready(address):** A top-level API function to check if the result at a given address is available.

- **get(address):** A top-level API function to retrieve a result by its address (blocks or fails if not yet available, depending on configuration).

- **get_portal(root):** A top-level API function that returns a portal instance bound to a storage root (local folder, S3, etc.).

- **describe():** A method on portals returning a pandas DataFrame snapshot of the portal state (e.g., cached results, queues, workers).

- **fix_kwargs(...):** A method on function wrappers (e.g., `PureFn`) that partially applies named arguments, returning a new callable with those parameters fixed.

## 6. Notes

- Only named arguments are allowed for decorated functions to ensure canonical argument packing and deterministic addressing.
- Source code changes in pure functions are tracked; changing code requires fresh execution for the new version, while preserving results from older versions.
