"""Utility for generating extended object identifiers.

Provides a function to build detailed identifier strings that include
module, class, and object name information.
"""
from typing import Any
import functools

from persidict import replace_unsafe_chars


def _safe_getattr(obj: Any, name: str):
    """Safely retrieve an attribute, returning None if any error occurs.

    This function catches all Exceptions during attribute access to handle
    properties or descriptors that might raise errors (e.g., during inspection
    of partially initialized objects).

    Args:
        obj: The object to inspect.
        name: The name of the attribute to retrieve.

    Returns:
        The attribute value, or None if the attribute is missing or accessing
        it raises an exception.
    """
    try:
        return getattr(obj, name, None)
    except Exception:
        return None


def get_long_infoname(x: Any, drop_unsafe_chars: bool = True) -> str:
    """Build a string with extended information about an object and its type.

    Creates a detailed identifier string that includes the module, class name,
    and object name (if available) of the given object.

    Args:
        x: The object for which to generate the information string.
        drop_unsafe_chars: If True, replaces unsafe characters with underscores
            using the persidict.replace_unsafe_chars function. Defaults to True.

    Returns:
        A string containing extended information about the object, including
        its module, class name, and object name (when available). Unsafe
        characters are replaced with underscores if drop_unsafe_chars is True.
    """
    if x is None:
        return "builtins.NoneType"
    if isinstance(x, (int, str, float, bool, bytes)):
        return "builtins." + type(x).__name__

    if isinstance(x, (functools.partial, functools.partialmethod)):
        base = get_long_infoname(x.func, drop_unsafe_chars=False)
        name = f"{base}_{type(x).__name__}"
        return replace_unsafe_chars(name, replace_with="_") if drop_unsafe_chars else name

    type_x = type(x)

    module = _safe_getattr(x, "__module__") or _safe_getattr(type_x, "__module__")
    type_name = _safe_getattr(type_x, "__qualname__") or _safe_getattr(type_x, "__name__")
    obj_name = _safe_getattr(x, "__qualname__") or _safe_getattr(x, "__name__")

    parts = [part for part in [module, type_name, obj_name] if part]
    if not parts:
        long_name = repr(type_x)
    else:
        long_name = ".".join(parts)

    if drop_unsafe_chars:
        long_name = replace_unsafe_chars(long_name, replace_with="_")

    return long_name
