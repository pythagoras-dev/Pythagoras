from typing import Any

from .data_portal_core_classes import HashAddr

def ready(obj) -> bool:
    """Return True if all objects in the data structure are ready."""
    return _ready(obj)

def _ready(obj, seen=None):
    """Return True if all objects in the data structure are ready."""
    if seen is None:
        seen = set()

    if id(obj) in seen:
        return True

    seen.add(id(obj))

    if isinstance(obj, HashAddr):
        return obj.ready
    elif isinstance(obj, (list,tuple)):
        return all(_ready(item, seen) for item in obj)
    elif isinstance(obj, dict):
        return all(_ready(value, seen) for key, value in obj.items())
    else:
        return True


def get(obj:Any) -> Any:
    """Return copy of data structure with addresses replaced with objects."""
    return _get(obj)


def _get(obj:Any, seen=None)->Any:
    """Return copy of data structure with addresses replaced with objects."""
    if seen is None:
        seen = dict()

    if id(obj) in seen:
        return seen[id(obj)]

    # For mutable objects that could contain circular references,
    # add a placeholder to break recursion
    if isinstance(obj, (list, dict)):
        # Create an empty container of the same type as a placeholder
        placeholder = type(obj)()
        seen[id(obj)] = placeholder

        if isinstance(obj, list):
            result = [_get(item, seen) for item in obj]
            # Update the placeholder with the actual values
            placeholder.extend(result)
            return placeholder
        elif isinstance(obj, dict):
            result = {key: _get(value, seen) for key, value in obj.items()}
            # Update the placeholder with the actual values
            placeholder.update(result)
            return placeholder

    if isinstance(obj, HashAddr):
        result = obj.get()
    elif isinstance(obj, tuple):
        result = tuple(_get(item, seen) for item in obj)
    else:
        result = obj

    seen[id(obj)] = result
    return result