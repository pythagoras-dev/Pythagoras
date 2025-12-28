"""Utilities for checking readiness and retrieving nested data structures.

This module provides two main functions for working with data structures that
contain HashAddr/ValueAddr objects:

- ready(): Recursively checks if all addresses in a nested structure are ready
  for retrieval (i.e., values are available in at least one portal).
- get(): Recursively retrieves values for all addresses in a nested structure,
  returning a fully resolved copy of the original structure.

Both functions handle cycles safely through memoization and support common
Python containers (lists, tuples, dicts). Atomic types (str, bytes, range)
are treated as leaf nodes and returned as-is.
"""
import collections
from typing import Any

from .data_portal_core_classes import HashAddr


def ready(obj) -> bool:
    """Check if all addresses in a nested structure are ready for retrieval.

    Recursively traverses the structure to verify that every HashAddr/ValueAddr
    is ready (i.e., its value is available in at least one known portal). Atomic
    types like strings and bytes are considered ready by default. Container types
    (lists, tuples, dicts) are recursed into.

    This is useful for checking preconditions before performing bulk retrievals
    or for validating that distributed computations have completed.

    Args:
        obj: Any Python object, possibly containing nested HashAddr/ValueAddr objects
            within lists, tuples, or dictionaries.

    Returns:
        True if all contained addresses are ready (or if obj contains no addresses),
        False if any address is not ready.

    Example:
        >>> data = [ValueAddr(1), ValueAddr(2), {"key": ValueAddr(3)}]
        >>> if ready(data):
        ...     values = get(data)
    """
    return _ready_impl(obj)

def _ready_impl(obj, seen=None):
    """Implementation helper for ready() with cycle protection.

    Traverses objects depth-first, tracking visited objects to handle cycles.
    Returns True for atomic types, recursively checks containers, and evaluates
    HashAddr.ready for address objects.

    Args:
        obj: Object under inspection.
        seen: Set of object ids already visited (prevents infinite loops on cycles).

    Returns:
        True if obj and all nested addresses are ready.
    """
    if seen is None:
        seen = set()
    elif id(obj) in seen:
        return True

    seen.add(id(obj))

    if isinstance(obj, (str,range, bytearray, bytes)):
        return True
    elif isinstance(obj, HashAddr):
        return obj.ready
    elif isinstance(obj,(list,tuple)):
        return all(_ready_impl(item, seen) for item in obj)
    elif isinstance(obj, dict):
        return all(_ready_impl(value, seen) for key, value in obj.items())
    else:
        return True

    # TODO: decide how to deal with Sequences/Mappings
    # elif isinstance(obj, collections.abc.Sequence):
    #     raise TypeError("Unsupported Sequence type: " + str(type(obj)))
    # elif isinstance(obj, collections.abc.Mapping):
    #     raise TypeError("Unsupported Mapping type: " + str(type(obj)))


def get(obj:Any) -> Any:
    """Recursively resolve all addresses in a nested structure.

    Creates a deep copy of the structure where every HashAddr/ValueAddr is
    replaced with its actual value (retrieved via .get()). Container topology
    is preserved: lists remain lists, dicts remain dicts, etc. Cycles are
    handled through memoization.

    This is the primary way to bulk-retrieve values from complex data structures
    that contain multiple addresses, such as the results of distributed computations.

    Args:
        obj: Any Python object or nested structure. Can contain HashAddr/ValueAddr
            objects at any depth within lists, tuples, or dictionaries.

    Returns:
        A copy of obj with all addresses replaced by their concrete values. Atomic
        types and non-address objects are returned as-is (or copied for containers).

    Example:
        >>> addr1 = ValueAddr([1, 2, 3])
        >>> addr2 = ValueAddr({"x": 10})
        >>> structure = {"data": addr1, "config": addr2}
        >>> resolved = get(structure)
        >>> resolved  # {"data": [1, 2, 3], "config": {"x": 10}}
    """
    return _get_impl(obj)


def _get_impl(obj:Any, seen=None)->Any:
    """Implementation helper for get() with cycle protection and memoization.

    Performs depth-first traversal, creating placeholders for mutable containers
    to break cycles, then filling them recursively. For HashAddr objects, calls
    .get() to retrieve the value. Preserves object identity for cyclic structures.

    Args:
        obj: Object to resolve.
        seen: Dict mapping object ids to their resolved copies (prevents infinite
            recursion on cycles).

    Returns:
        The resolved object or a structure with all addresses replaced by values.
    """
    if seen is None:
        seen = dict()

    if id(obj) in seen:
        return seen[id(obj)]

    # For mutable objects that could contain circular references,
    # add a placeholder to break recursion
    if isinstance(obj, (str, range, bytearray, bytes)):
        return obj
    elif isinstance(obj, (list, dict)):
        # Create an empty container of the same type as a placeholder
        placeholder = type(obj)()
        seen[id(obj)] = placeholder

        if isinstance(obj, list):
            result = [_get_impl(item, seen) for item in obj]
            # Update the placeholder with the actual values
            placeholder.extend(result)
            return placeholder
        elif isinstance(obj, dict):
            result = {key: _get_impl(value, seen) for key, value in obj.items()}
            # Update the placeholder with the actual values
            placeholder.update(result)
            return placeholder
    elif isinstance(obj, HashAddr):
        result = obj.get()
    elif isinstance(obj, tuple):
        result = tuple(_get_impl(item, seen) for item in obj)
    else:
        result = obj

    # TODO: decide how to deal with Sequences/Mappings
    # elif isinstance(obj, collections.abc.Sequence):
    #     raise TypeError("Unsupported Sequence type: " + str(type(obj)))
    # elif isinstance(obj, collections.abc.Mapping):
    #     raise TypeError("Unsupported Mapping type: " + str(type(obj)))

    seen[id(obj)] = result
    return result