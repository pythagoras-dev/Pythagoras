import collections
from typing import Any

from .data_portal_core_classes import HashAddr


def ready(obj) -> bool:
    """Return True if all objects in the data structure are ready."""
    return _ready_impl(obj)

def _ready_impl(obj, seen=None):
    """Return True if all objects in the data structure are ready."""
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
    """Return copy of data structure with addresses replaced with objects."""
    return _get_impl(obj)


def _get_impl(obj:Any, seen=None)->Any:
    """Return copy of data structure with addresses replaced with objects."""
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