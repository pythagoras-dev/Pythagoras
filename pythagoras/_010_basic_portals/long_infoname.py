from typing import Any

from persidict import replace_unsafe_chars


def get_long_infoname(x:Any, drop_unsafe_chars:bool = True) -> str:
    """Build a string with extended information about an object and its type"""

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
