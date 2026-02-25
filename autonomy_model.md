# Pythagoras Autonomy Model

Pythagoras requires that distributed functions be self-contained — carrying everything they need to execute on any machine. This document defines the autonomy constraints, how they are enforced, and how to work within them.

## Why autonomy exists

Distributed execution requires shipping code to remote workers. If a function references module-level imports, closure variables, or global state, those references break when the function is serialized and sent elsewhere. Pythagoras solves this by requiring that distributed functions be **autonomous**: all dependencies must be explicitly declared inside the function body, making the function a self-contained unit of computation.

Autonomy and purity are **independent properties**: autonomy makes functions distributable (self-contained code can be shipped anywhere); purity makes them memoizable (deterministic results can be cached forever). An autonomous function that calls `random.random()` is autonomous but not pure. A function using `math.sqrt` via a module-level import is pure but not autonomous. `@pure` requires both: autonomy is enforced by AST analysis; purity is the programmer's semantic contract.

Autonomy alone does not make caching safe — an autonomous but impure function could return different results for the same inputs. Caching requires both autonomy (so the function's code fully determines *what runs*) and purity (so the function's inputs fully determine *the result*).

---

## Two levels of constraint: ordinarity and autonomy

Pythagoras enforces constraints at two levels, each building on the previous one.

### Ordinarity (enforced by `@ordinary` and all higher decorators)

A function must satisfy **all** of these to be "ordinary":

| Constraint | Why |
|---|---|
| Must be a plain function (`def`, not `class`, not method) | Ensures a uniform callable model |
| Not a lambda | Lambdas lack a proper name, making identification and source extraction unreliable |
| Not a closure (no captured variables) | Captured variables are hidden state that breaks serialization |
| Not async (`async def` forbidden) | Async requires an event loop — incompatible with the synchronous execution model |
| No positional-only parameters (`/` forbidden) | Canonical addressing requires all arguments to be keyword-addressable |
| No `*args` (unlimited positional args forbidden) | Same reason — all arguments must have explicit names |
| No default parameter values | Defaults create ambiguity in canonical call representations; every argument must be explicitly provided |

**Enforcement:** `assert_ordinarity()` in `_310_ordinary_code_portals/function_processing.py` checks all constraints at decoration time. Violations raise `FunctionError`.

### Autonomy (enforced by `@autonomous`, `@guarded`, and `@pure`)

On top of ordinarity, an autonomous function must additionally satisfy:

| Constraint | Why |
|---|---|
| No `global` declarations | Global references bind to module-level state that doesn't travel with the function |
| No `nonlocal` declarations | Nonlocal references bind to enclosing scope state (closures) |
| No `yield` / `yield from` | Generators maintain persistent state across calls, incompatible with single-shot execution |
| No relative imports (`from . import ...`) | Relative imports depend on package structure that may not exist on the remote machine |
| All external names must be imported inside the function body | External name references that aren't builtins, imported inside the body, or in the allowed set are forbidden |

**Enforcement:** `NamesUsageAnalyzer` in `_340_autonomous_code_portals/names_usage_analyzer.py` performs a full AST traversal at decoration time. Violations raise `FunctionError` with a message identifying the offending names.

---

## The AST analysis in detail

When `AutonomousFn.__init__()` runs, it invokes `_analyze_names_in_function()`, which:

1. **Normalizes** the source code (see "Source code normalization" below).
2. **Parses** the normalized source into an AST.
3. **Traverses** the AST with `NamesUsageAnalyzer`, classifying every name into one of:

| Classification | Meaning | Example |
|---|---|---|
| `local` | Bound inside the function (parameters, assignments, for-loop targets, exception handler names) | `x` in `def f(x):` or `y = 5` |
| `imported` | Explicitly imported inside the function body | `np` in `import numpy as np` |
| `explicitly_global_unbound_deep` | Declared with `global` keyword | `global MY_VAR` |
| `explicitly_nonlocal_unbound_deep` | Declared with `nonlocal` keyword | `nonlocal counter` |
| `unclassified_deep` | Referenced but not bound, imported, or declared — potential external dependency | `math` in `math.sqrt(x)` without importing `math` |

4. **Checks** that `explicitly_global_unbound_deep` is empty.
5. **Checks** that `explicitly_nonlocal_unbound_deep` is empty.
6. **Checks** that there are no `yield` statements.
7. **Checks** that there are no relative imports.
8. **Computes** the set of names requiring imports: `explicitly_global_unbound_deep` ∪ `unclassified_deep` − builtins − allowed names − the function's own name.
9. **Rejects** the function if this set is non-empty.

### Scope handling for nested constructs

The analyzer handles Python's scoping rules:

- **Nested functions and lambdas**: Analyzed in a fresh `NamesUsageAnalyzer` scope. Unresolved names are filtered against the parent's accessible names before being reported.
- **Nested classes**: Base classes and decorators are evaluated in the parent scope; the class body gets its own scope.
- **Comprehensions**: Treated as implicit function scopes (Python 3 semantics) to prevent iterator variable leakage.

### Allowed names in the autonomous context

A small set of names is always available without explicit import:

| Name | Value |
|---|---|
| All Python builtins | `print`, `len`, `range`, `dict`, etc. |
| The function's own name | Enables recursion |
| `pth` | The `pythagoras` module itself |

---

## Source code normalization

Before hashing or autonomy analysis, source code is normalized to a canonical form. This ensures that cosmetic changes (reformatting, adding comments) don't affect cache keys or analysis results.

The normalization pipeline:

1. **Extract** source via `inspect.getsource()` (or accept a string).
2. **Dedent** and remove empty lines.
3. **Parse** into AST; verify a single `def` at the top level.
4. **Remove Pythagoras decorators** (`@ordinary`, `@autonomous`, `@pure`, etc.) from the AST. At most one decorator is allowed.
5. **Remove type annotations** (parameter annotations, return annotations, variable annotations).
6. **Remove docstrings** (leading string expressions in function/class/module bodies; empty bodies get `pass`).
7. **Format** with `autopep8` for consistent PEP 8 style.

The result is a deterministic string representation that changes only when the function's actual logic changes. This normalized form is used for:

- Content-hash computation (cache keys in `PureFnExecutionResultAddr`).
- Autonomy analysis (AST traversal).
- Display and comparison.

---

## Allowed vs. forbidden patterns

### ✅ Allowed

```python
@pure()
def compute_distance(x1, y1, x2, y2):
    import math                          # Import inside body ✅
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

@pure()
def process_data(data):
    import pandas as pd                  # Import inside body ✅
    df = pd.DataFrame(data)             # Local variable ✅
    return df.describe().to_dict()

@pure()
def recursive_factorial(n):
    if n <= 1:                           # Recursion via own name ✅
        return 1
    return n * recursive_factorial(n=n-1)

@pure()
def with_helper(values):
    def mean(xs):                        # Nested helper function ✅
        return sum(xs) / len(xs)
    return mean(values)
```

### ❌ Forbidden

```python
import numpy as np                       # Module-level import
@pure()
def bad_external_ref(x):
    return np.sqrt(x)                    # ❌ "np" is an unresolved external name

@pure()
def bad_global(x):
    global CONFIG                        # ❌ global declaration
    return CONFIG[x]

@pure()
def bad_nonlocal(x):
    nonlocal counter                     # ❌ nonlocal declaration
    counter += 1
    return x + counter

@pure()
def bad_generator(x):
    yield x * 2                          # ❌ yield statement

@pure()
def bad_relative_import(x):
    from . import utils                  # ❌ relative import
    return utils.process(x)

def bad_default(x=10):                   # ❌ default value (ordinarity violation)
    return x * 2

def bad_positional(x, /):               # ❌ positional-only param (ordinarity violation)
    return x * 2

bad_lambda = lambda x: x * 2            # ❌ lambda (ordinarity violation)
```

---

## Common patterns for working within autonomy

### Move imports inside the function body

The most common adaptation. Every function imports exactly what it needs:

```python
@pure()
def train_model(data, n_estimators):
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=n_estimators)
    model.fit(data["X"], data["y"])
    return model
```

### Pass configuration as arguments, not globals

Instead of reading from a global config object, pass settings explicitly:

```python
@pure()
def fetch_and_process(url, timeout, max_retries):
    import requests
    response = requests.get(url, timeout=timeout)
    return response.json()
```

### Use the `installed_packages` requirement for dependencies

Ensure packages are available on the remote machine before execution:

```python
from pythagoras import pure, autonomous, installed_packages

@pure(requirements=[installed_packages("scikit-learn", "pandas")])
def analyze(dataset_path):
    import pandas as pd
    from sklearn.cluster import KMeans
    df = pd.read_csv(dataset_path)
    return KMeans(n_clusters=3).fit_predict(df)
```

### Use `fix_kwargs` for partial application

Instead of closures, use `fix_kwargs` to pre-bind arguments:

```python
@pure()
def process_item(item, config_path):
    import json
    with open(config_path) as f:
        config = json.load(f)
    return transform(item, config)

# Create a specialized version with fixed config
process_with_default_config = process_item.fix_kwargs(
    config_path="/shared/config.json")
```
