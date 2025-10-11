import collections
from typing import Any

from .data_portal_core_classes import HashAddr


def ready(obj) -> bool:
    """Check readiness of a possibly nested data structure.

    Recursively inspects the structure and returns True only if every
    HashAddr/ValueAddr contained is ready. Strings and bytes-like objects are
    treated as atomic. Lists, tuples, and dicts are traversed recursively.

    Args:
        obj: Any Python object, possibly a nested combination of lists, tuples,
            and dicts containing HashAddr/ValueAddr objects.

    Returns:
        bool: True if all contained addresses are ready; False otherwise.
    """
    return _ready_impl(obj)

def _ready_impl(obj, seen=None):
    """Implementation helper for ready() with cycle protection.

    Args:
        obj: Object under inspection.
        seen: A set of object ids already visited to prevent infinite loops
            on cyclic graphs.

    Returns:
        bool: True if obj and all nested addresses are ready.
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
    """Deep-copy a structure, replacing HashAddr/ValueAddr with values.

    Traverses the structure and replaces every address with the value
    obtained via .get(), preserving container topology. Handles cycles by
    memoizing objects during traversal.

    Args:
        obj: Any Python object or nested structure containing addresses.

    Returns:
        Any: A copy of obj with all addresses resolved into concrete values.
    """
    return _get_impl(obj)


def _get_impl(obj:Any, seen=None)->Any:
    """Implementation helper for get() with cycle protection and memoization.

    Args:
        obj: Object to resolve.
        seen: A dict mapping visited object ids to their resolved copies,
            used to preserve identities and break cycles.

    Returns:
        Any: The resolved object or a structure containing resolved values.
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