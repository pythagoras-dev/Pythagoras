# Pythagoras docstrings and comments guidelines

This document defines the standards for writing docstrings and comments in the `Pythagoras` project. Following these guidelines ensures consistency, maintainability, and clarity across the codebase.

## Core principles

1. **Use Google-style docstrings** for all public modules, classes, methods, and functions.
2. **Follow PEP 257** (Docstring Conventions) and **PEP 8** (Style Guide for Python Code).
3. **Focus on WHAT and WHY** in comments and docstrings. Explain HOW only when the implementation is non-obvious 
  or uses advanced techniques. Typically, docstrings and comments should explain code intent 
  and implementation strategies, not implementation details
4. **Write for the reader**: assume the reader understands Python but may be unfamiliar with this specific codebase.

---

## Docstrings

### When to write docstrings

**Always provide docstrings for:**
- Public modules (at the top of the file)
- Public classes
- Public functions and methods
- Non-trivial private functions that implement complex logic

**You may omit docstrings for:**
- Trivial private helper functions with self-explanatory names (e.g., `_is_valid_key`)
- Standard dunder methods like `__repr__`, `__str__` when behavior is obvious
- Test functions (though a brief one-liner can help clarify intent)

### Google-style docstring format

Google-style docstrings are clean, readable, and well-supported by documentation tools like Sphinx (with the Napoleon extension).

#### Basic structure

```python
def function_name(arg1, arg2):
    """One-line summary that fits on one line.

    Optional longer description that provides more context about what
    the function does, why it exists, and any important behavioral notes.
    This can span multiple paragraphs if needed.

    Args:
        arg1: Description of arg1. Type should be in type hints, not here.
        arg2: Description of arg2. Explain the purpose, not just the type.

    Returns:
        Description of the return value. Focus on what it represents.

    Raises:
        ValueError: When arg1 is negative.
        KeyError: When arg2 is not found in the internal mapping.

    Example:
        >>> function_name(5, "key")
        42
    """
```

#### Module-level docstrings

Place a module docstring at the very top of each file (after the shebang and encoding, if present, but before imports):

```python
"""Brief one-line description of the module.

Longer description explaining the module's purpose, main classes/functions,
and how it fits into the overall package architecture.
"""

import os
import sys
```

#### Class docstrings

```python
class PersistentDict:
    """A dictionary that persists data to disk.

    This class provides a dict-like interface where all changes are
    automatically saved to the filesystem. It supports standard dict
    operations and ensures data durability across program restarts.

    Args:
        base_dir: Directory where the dictionary data will be stored.
        file_name: Optional name for the storage file. Defaults to a
            generated name based on the instance.

    Attributes:
        base_dir: The directory path where data is persisted.
        file_name: The name of the backing storage file.
    """
```

**Note:** The `Args:` section in a class docstring describes `__init__` parameters.

#### Method and function docstrings

```python
def load_from_disk(self, path):
    """Load dictionary contents from a file on disk.

    Reads and deserializes data from the specified path, replacing
    the current in-memory state. If the file does not exist, raises
    FileNotFoundError rather than initializing an empty dict.

    Args:
        path: Path to the file containing serialized dictionary data.

    Returns:
        The number of entries loaded.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file content is not valid serialized data.
    """
```

#### Properties

For `@property` decorated methods, write the docstring as if it's an attribute:

```python
@property
def is_empty(self):
    """True if the dictionary contains no items, False otherwise."""
    return len(self) == 0
```

### Section order

Use sections in this order (omit any that don't apply):

1. Summary (one line)
2. Extended description (optional)
3. `Args:`
4. `Returns:` or `Yields:` (for generators)
5. `Raises:`
6. `Example:` or `Examples:` (optional but encouraged for non-obvious usage)
7. `Note:` or `Warning:` (if needed)

### Type hints vs. docstrings

**Use type hints in function signatures** for all parameters and return values. Do not repeat type information in the docstring:

✅ **Good:**
```python
def add_item(self, key: str, value: int) -> None:
    """Add an item to the dictionary.

    Args:
        key: The unique identifier for the item.
        value: The numeric value to store.
    """
```

❌ **Bad:**
```python
def add_item(self, key: str, value: int) -> None:
    """Add an item to the dictionary.

    Args:
        key (str): The unique identifier for the item.
        value (int): The numeric value to store.
    """
```

If a parameter accepts multiple types or has constraints, explain in the description:

```python
def set_timeout(self, seconds: float | None) -> None:
    """Set the operation timeout.

    Args:
        seconds: Timeout duration in seconds, or None to disable timeout.
    """
```

### Focus on WHAT and WHY

Docstrings should explain:
- **WHAT** the function/class does
- **WHY** it exists or why certain design choices were made
- **HOW** only when the approach is non-obvious

✅ **Good:**
```python
def normalize_path(self, path: str) -> str:
    """Convert path to canonical form for cross-platform compatibility.

    Ensures consistent path handling on Windows, macOS, and Linux by
    resolving relative references and standardizing separators.

    Args:
        path: A filesystem path that may contain relative components.

    Returns:
        Absolute path with OS-appropriate separators.
    """
```

❌ **Bad (too focused on HOW):**
```python
def normalize_path(self, path: str) -> str:
    """Convert path to canonical form.

    First calls os.path.abspath, then os.path.normpath, then replaces
    backslashes with forward slashes on Windows.

    Args:
        path: A filesystem path.

    Returns:
        Normalized path.
    """
```

---

## Comments

Comments should clarify **intent**, **reasoning**, and **non-obvious behavior**. Avoid stating the obvious.

### Inline comments

Use inline comments sparingly. Place them on the same line as the code or on the line immediately above.

✅ **Good (explains WHY):**
```python
# Delay to ensure distinct timestamps on filesystems with 1-second granularity
time.sleep(1.1)
```

✅ **Good (explains WHAT in a non-obvious context):**
```python
# UNC paths on Windows require special handling
if path.startswith("\\\\"):
    return self._handle_unc_path(path)
```

❌ **Bad (states the obvious):**
```python
# Increment counter
counter += 1
```

❌ **Bad (explains trivial HOW):**
```python
# Loop through all items
for item in items:
    process(item)
```

### Block comments

Use block comments for explaining complex algorithms, edge cases, or design decisions:

```python
# S3 has eventual consistency for overwrites and deletes. To avoid
# serving stale data, we use a local cache with TTL-based invalidation.
# Cache entries expire after CACHE_TTL seconds, forcing a fresh read
# from S3. This trades off latency for consistency guarantees.
if self._is_cache_stale(key):
    value = self._fetch_from_s3(key)
    self._update_cache(key, value)
```

### TODOs, FIXMEs, and NOTEs

Use standard tags for annotations:

```python
# TODO: Add support for nested directory structures.
# FIXME: Race condition when multiple processes write simultaneously.
# NOTE: This implementation assumes keys are ASCII strings.
```

Include a GitHub issue reference if applicable:
```python
# TODO(#123): Migrate to the new serialization format.
```

### Comments for non-obvious "HOW"

When implementation is tricky, explain HOW:

```python
def _generate_unique_id(self):
    """Generate a unique identifier for this dictionary instance.

    Uses a combination of timestamp, process ID, and random bytes to
    ensure uniqueness across concurrent processes and machine restarts.
    """
    # Combine timestamp (microseconds) with PID and random entropy to avoid
    # collisions even when many processes start simultaneously.
    ts = int(time.time() * 1e6)
    pid = os.getpid()
    rand = secrets.token_hex(4)
    return f"{ts}_{pid}_{rand}"
```

### Avoid commented-out code

Don't leave large blocks of commented-out code in the repository. Use version control to preserve history.

✅ **Good:**
```python
def process_data(self, data):
    return self._new_algorithm(data)
```

❌ **Bad:**
```python
def process_data(self, data):
    # Old approach:
    # result = []
    # for item in data:
    #     result.append(transform(item))
    # return result
    return self._new_algorithm(data)
```

If you must temporarily disable code during development, use a clear comment explaining why:

```python
# Temporarily disabled while investigating issue #456
# self._validate_integrity()
```

---

## Best practices from the Python community

1. **PEP 257 – Docstring Conventions**: All docstrings should be triple-quoted (`"""`), even one-liners. One-liners should have both quotes on the same line:
   ```python
   def get_name(self):
       """Return the name of this instance."""
   ```

2. **PEP 8 – Comments**: Comments should be complete sentences. The first word should be capitalized unless it's an identifier that begins with a lowercase letter.

3. **PEP 20 – The Zen of Python**: "Explicit is better than implicit." Write comments and docstrings that make your intentions clear.

4. **Consistency**: Match the style of existing code in the module. If the surrounding code uses certain phrasing or structure, follow it.

5. **Readability counts**: Prefer clarity over cleverness. If you need a comment to explain code, consider refactoring the code to be more self-explanatory first.

---

## Examples: Good vs. Bad

### Example 1: Function docstring

❌ **Bad:**
```python
def calculate(x, y):
    # This function calculates something
    return x * 2 + y
```

✅ **Good:**
```python
def calculate_score(attempts: int, bonus: int) -> int:
    """Calculate the final score based on attempts and bonus points.

    The score is computed as double the attempts plus any bonus points.
    This formula rewards efficiency (fewer attempts) while allowing
    bonuses to significantly impact the outcome.

    Args:
        attempts: Number of attempts taken to complete the task.
        bonus: Additional points awarded for special achievements.

    Returns:
        The calculated score.
    """
    return attempts * 2 + bonus
```

### Example 2: Inline comment

❌ **Bad:**
```python
result = value + 10  # Add 10 to value
```

✅ **Good:**
```python
# Add buffer size to account for header overhead
result = value + HEADER_SIZE
```

### Example 3: Class with complex behavior

✅ **Good:**
```python
class WriteOnceDict(dict):
    """A dictionary that prevents modification of existing keys.

    This class enforces write-once semantics: once a key is set, any
    attempt to modify or delete it raises an error. This is useful for
    configurations that must remain immutable after initialization.

    Args:
        initial_data: Optional mapping or iterable of key-value pairs
            to initialize the dictionary.

    Raises:
        ValueError: If attempting to modify or delete an existing key.

    Example:
        >>> d = WriteOnceDict({'a': 1})
        >>> d['b'] = 2  # OK
        >>> d['a'] = 3  # Raises ValueError
    """
```

---

## Summary

- **Always use Google-style docstrings** for public APIs.
- **Explain WHAT and WHY**, not HOW (unless non-obvious).
- **Use type hints** in signatures; don't duplicate them in docstrings.
- **Write comments that add value**, not noise.
- **Be consistent** with the existing codebase.
