# Pythagoras type hints guidelines

Type hints are mandatory for all public APIs in `Pythagoras`. They improve code readability, enable IDE autocomplete and refactoring, and allow static type checkers to catch bugs before runtime.

## When to use type hints

**Always provide type hints for:**
- All function and method parameters
- All function and method return values
- Class attributes (using annotations)
- Module-level constants

**Type hints in docstrings:**
- Never duplicate type information in docstrings—types belong in signatures only
- Use docstring parameter descriptions to explain constraints, valid ranges, or semantic meaning

## Modern Python syntax

Use modern type hint syntax available in Python 3.11+:

**Union types** with `|`:
```python
def process(value: str | int) -> str:
    """Process a string or integer value."""
    return str(value)
```

**Optional types** with `| None`:
```python
def find_user(user_id: int) -> User | None:
    """Return user if found, None otherwise."""
    ...
```

**Built-in generic collections** (no imports needed):
```python
def merge_data(items: list[str], mapping: dict[str, int]) -> tuple[str, ...]:
    """Merge items using the provided mapping."""
    ...
```

❌ **Avoid legacy syntax:**
- `Union[str, int]` → use `str | int`
- `Optional[str]` → use `str | None`
- `List[str]`, `Dict[str, int]` → use `list[str]`, `dict[str, int]`

## Accept flexible inputs, return concrete types

Follow the robustness principle: accept broad types as inputs, return specific types as outputs.

**For function parameters**, use abstract types from `collections.abc` to accept any compatible input:
- `Sequence[T]` accepts lists, tuples, and other sequences
- `Iterable[T]` accepts any iterable (lists, sets, generators, etc.)
- `Mapping[K, V]` accepts dicts and other mappings
- `Callable[[ArgTypes], ReturnType]` accepts any callable

**For return values**, use concrete types so callers know exactly what they get:
- Return `list[T]`, not `Sequence[T]`
- Return `dict[K, V]`, not `Mapping[K, V]`
- Return `set[T]`, not `Set[T]`

**Example:**
```python
from collections.abc import Sequence, Mapping

def format_items(
    items: Sequence[str],
    config: Mapping[str, bool] | None = None,
) -> list[str]:
    """Format items according to configuration.
    
    Args:
        items: Items to format (accepts list, tuple, etc.).
        config: Optional formatting configuration.
        
    Returns:
        List of formatted strings.
    """
    return [item.upper() for item in items]
```

## Avoiding `Any`

Avoid `Any` whenever possible, as it effectively disables type checking.

- Use `object` if the value can be anything and you don't need to access its attributes.
- Use `TypeVar` (generics) if the type is unknown but should be consistent/preserved.
- Use `Protocol` (structural subtyping) if you need specific methods/attributes but don't care about the inheritance hierarchy.

## Type Aliases

Use type aliases to simplify complex signatures and give semantic meaning to types:

```python
UserId = int
SessionToken = str
AuthContext = tuple[UserId, SessionToken]

def validate_session(context: AuthContext) -> bool:
    ...
```

---

## Summary

- **Use modern type hints** (e.g. `str | None`) in signatures.
- **Follow Postel's Law** for types: generic inputs (`Sequence`), concrete outputs (`list`).
- **Be consistent** with the existing codebase.
