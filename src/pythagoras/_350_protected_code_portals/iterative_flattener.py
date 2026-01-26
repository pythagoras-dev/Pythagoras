from collections.abc import Iterable
from typing import Any, Iterator
from collections import deque

from .._110_supporting_utilities import get_long_infoname

_ATOMIC_TYPES = (str, bytes, bytearray, memoryview
    , int, float, complex, bool, type(None))


def _is_flattenable(obj: Any) -> bool:
    """
    True for containers that should be walked through when flattening.

    Strings and bytes are *not* treated as containers – they are atomic.
    """

    if isinstance(obj, _ATOMIC_TYPES):
        return False
    else:
        return isinstance(obj, Iterable)


def flatten_iterative(nested_iterative: Iterable[Any]) -> list[Any]:
    """
    General-purpose, *iterative* flattener.

    This is a stricter but more flexible version of :func:`flatten_list` that:

    * Accepts any iterable (lists, tuples, sets, generators, numpy arrays, …).
    * Treats *only* true iterables (excluding ``str``/``bytes``) as containers.
    * Detects self-referential iterables to avoid infinite loops.
    * Preserves original left-to-right element order.

    Parameters
    ----------
    nested_iterative:
        The possibly nested iterable to flatten.

    Returns
    -------
    list
        A flat list of values.

    Raises
    ------
    TypeError
        If *nested_iterative* is **not** an iterable.
    ValueError
        For cyclic/self-referential structures.

    Examples
    --------
    >>> flatten_iterative([1, (2, {3, 4}), 5])
    [1, 2, 3, 4, 5]
    >>> flatten_iterative([[["a"], "b"], "c"])
    ['a', 'b', 'c']
    """
    if not isinstance(nested_iterative, Iterable):
        raise TypeError(
            f"Expected an iterable, got {get_long_infoname(nested_iterative)}"
        )

    flattened: list[Any] = []
    # Stack stores tuples of (iterator, obj_id) – we track ids only
    stack: list[tuple[Any, int]] = list([(iter(nested_iterative), id(nested_iterative))])
    # Track object ids in the current traversal path to detect cycles
    path: set[int] = {id(nested_iterative)}

    sentinel = object()

    while stack:
        parent_iter, parent_id = stack[-1]

        item = next(parent_iter, sentinel)
        if item is sentinel:
            stack.pop()
            path.remove(parent_id)
            continue

        if _is_flattenable(item):
            obj_id = id(item)
            if obj_id in path:
                raise ValueError("Cyclic reference detected during flattening")

            child_iter = item if isinstance(item, Iterator) else iter(item)
            path.add(obj_id)
            stack.append((child_iter, obj_id))
        else:
            flattened.append(item)

    return flattened