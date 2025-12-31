"""
ready_and_get.py – utilities for HashAddr-aware tree traversal
--------------------------------------------------------------

This module offers two convenience helpers that can walk arbitrary
Python object graphs looking for ``HashAddr`` / ``ValueAddr`` objects
defined in *pythagoras* data-portals:

• ready(obj) – depth-first check that *every* address embedded in
  ``obj`` is ``ready`` (i.e. its value can be fetched from at least one
  known portal).

• get(obj)   – deep-copy of ``obj`` where every address is replaced by
  its resolved value (via ``.get()``).  Container topology and identity
  are preserved and cycles are handled correctly.

The functions understand:

    – atomic immutable scalars: str, bytes, bytearray, range
    – built-in containers: list, tuple, dict
    – any ``collections.abc.Sequence`` / ``Mapping`` subclass *provided
      that* we can construct an empty placeholder of the same class.
      Otherwise a clear ``TypeError`` is raised so that client code can
      register a custom handler.

They are intentionally dependency-free apart from ``HashAddr``.
"""
from __future__ import annotations

from collections.abc import Mapping as _Mapping, Sequence as _Sequence
from typing import Any

from .data_portal_core_classes import HashAddr

# --------------------------------------------------------------------------- #
# Helper utilities                                                            #
# --------------------------------------------------------------------------- #

# Sequence subclasses that should *not* be traversed (act as atoms)
_ATOMIC_SEQ_TYPES: tuple[type, ...] = (str, bytes, bytearray, range)


def _is_atomic(obj: Any) -> bool:
    """Return True if *obj* is considered a leaf for recursion purposes."""
    return isinstance(obj, _ATOMIC_SEQ_TYPES)


def _make_empty_clone(container: Any) -> Any | None:
    """
    Attempt to create an *empty* instance of ``type(container)`` so that we
    can break cycles while descending.  Returns the clone or ``None`` if it
    cannot be built safely.
    """
    cls = type(container)
    # Fast-path for common containers
    if cls in (list, dict, tuple, set):
        return cls()
    try:
        return cls()  # hope for no-arg constructor
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# ready()                                                                     #
# --------------------------------------------------------------------------- #
def ready(obj: Any) -> bool:
    """Recursively verify that **all** HashAddr objects inside *obj* are ready."""
    return _ready_impl(obj, seen=set())


def _ready_impl(obj: Any, *, seen: set[int]) -> bool:
    if id(obj) in seen:
        return True
    seen.add(id(obj))

    if _is_atomic(obj):
        return True
    if isinstance(obj, HashAddr):
        return obj.ready
    if isinstance(obj, (list, tuple)):
        return all(_ready_impl(item, seen=seen) for item in obj)
    if isinstance(obj, dict):
        return all(_ready_impl(k, seen=seen) and _ready_impl(v, seen=seen)
                   for k, v in obj.items())
    if isinstance(obj, _Mapping):
        return all(_ready_impl(k, seen=seen) and _ready_impl(v, seen=seen)
                   for k, v in obj.items())
    if isinstance(obj, _Sequence) and not _is_atomic(obj):
        return all(_ready_impl(item, seen=seen) for item in obj)
    # Fallback: treat as leaf
    return True


# --------------------------------------------------------------------------- #
# get()                                                                       #
# --------------------------------------------------------------------------- #
def get(obj: Any) -> Any:
    """Return a deep copy of *obj* with every HashAddr replaced by its value."""
    return _get_impl(obj, seen={})


def _get_impl(obj: Any, *, seen: dict[int, Any]) -> Any:
    """
    Depth-first copy of *obj* where every HashAddr is replaced by its value.
    Cycles are handled via the *seen* memo-dict.
    """
    # ➊ Cycle guard ­­– return the already-built clone if we revisited the same id
    if id(obj) in seen:
        return seen[id(obj)]

    # ➋ Primitive atomic “leaves” (strings, bytes, …)
    if _is_atomic(obj):
        return obj

    # ➌ Addresses MUST be handled *before* general tuple / sequence logic
    if isinstance(obj, HashAddr):
        value = obj.get()
        seen[id(obj)] = value
        return value

    # ------------------------------------------------------------------ #
    # Built-in containers with identity-preserving placeholders           #
    # ------------------------------------------------------------------ #
    if isinstance(obj, list):
        placeholder: list = []
        seen[id(obj)] = placeholder
        placeholder.extend(_get_impl(item, seen=seen) for item in obj)
        return placeholder

    if isinstance(obj, dict):
        placeholder: dict = {}
        seen[id(obj)] = placeholder
        for k, v in obj.items():
            placeholder[_get_impl(k, seen=seen)] = _get_impl(v, seen=seen)
        return placeholder

    if isinstance(obj, tuple):
        clone = tuple(_get_impl(item, seen=seen) for item in obj)
        seen[id(obj)] = clone
        return clone

    # ------------------------------------------------------------------ #
    # Generic Mapping / Sequence fall-backs                               #
    # ------------------------------------------------------------------ #
    if isinstance(obj, _Mapping):
        placeholder = _make_empty_clone(obj)
        if placeholder is None:
            raise TypeError(f"Cannot create empty placeholder for mapping type {type(obj)}")
        seen[id(obj)] = placeholder
        for k, v in obj.items():
            placeholder[_get_impl(k, seen=seen)] = _get_impl(v, seen=seen)
        return placeholder

    if isinstance(obj, _Sequence) and not _is_atomic(obj):
        placeholder = _make_empty_clone(obj)
        if placeholder is None:
            raise TypeError(f"Cannot create empty placeholder for sequence type {type(obj)}")
        seen[id(obj)] = placeholder
        items = [_get_impl(item, seen=seen) for item in obj]
        # Try to rebuild the original type; fall back gracefully
        try:
            rebuilt = type(obj)(items)
        except Exception:
            rebuilt = items
        if hasattr(placeholder, "extend"):          # mutable sequence
            placeholder.extend(items)
            rebuilt = placeholder
        return rebuilt

    # ------------------------------------------------------------------ #
    # Any other object – keep as-is                                       #
    # ------------------------------------------------------------------ #
    seen[id(obj)] = obj
    return obj