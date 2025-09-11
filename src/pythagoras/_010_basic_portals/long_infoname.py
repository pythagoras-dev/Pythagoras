from typing import Any

from persidict import replace_unsafe_chars


def get_long_infoname(x: Any, drop_unsafe_chars: bool = True) -> str:
    """Build a string with extended information about an object and its type.

    Creates a detailed identifier string that includes the module, class name,
    and object name (if available) of the given object. This is useful for
    creating unique identifiers for objects in the Pythagoras system.

    Args:
        x: The object for which to generate the information string.
        drop_unsafe_chars: If True, replaces unsafe characters with underscores
            using the persidict.replace_unsafe_chars function. Defaults to True.

    Returns:
        A string containing extended information about the object, including
        its module, class name, and object name (when available). Unsafe
        characters are replaced with underscores if drop_unsafe_chars is True.
    """

    name = str(type(x).__module__)

    if hasattr(type(x), "__qualname__"):
        name += "." + str(type(x).__qualname__)
    else:
        name += "." + str(type(x).__name__)

    if hasattr(x, "__qualname__"):
        name += "_" + str(x.__qualname__)
    elif hasattr(x, "__name__"):
        name += "_" + str(x.__name__)

    if drop_unsafe_chars:
        name = replace_unsafe_chars(name, replace_with="_")

    return name
