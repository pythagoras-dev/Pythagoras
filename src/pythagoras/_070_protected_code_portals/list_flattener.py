from typing import List, Any, Iterator


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """Flatten a nested list into a single-level list.

    This function flattens lists of arbitrary depth using an iterative
    (non-recursive) algorithm. Only values of type ``list`` are treated as
    containers to be expanded. Other iterable types (e.g., tuples, sets,
    strings, generators) are considered atomic values and are not traversed.

    Parameters:
    - nested_list: list
        A possibly nested Python list. Must be an instance of ``list``.

    Returns:
    - list
        A new list containing all elements from ``nested_list`` in their
        original left-to-right order, but with one level of nesting (flat).

    Raises:
    - TypeError: If ``nested_list`` is not a ``list`` instance.

    Notes:
    - Preserves the order of elements.
    - Supports unlimited nesting depth without recursion.
    - Cyclic references (e.g., a list that contains itself, directly or
      indirectly) will lead to an infinite loop.

    Examples:
    >>> flatten_list([1, [2, 3, [4]], 5])
    [1, 2, 3, 4, 5]
    >>> flatten_list([["a", ["b"]], "c"]) 
    ['a', 'b', 'c']
    >>> flatten_list([(1, 2), [3, 4]])
    [(1, 2), 3, 4]
    """
    if not isinstance(nested_list, list):
        raise TypeError(f"Expected list, got {type(nested_list).__name__}")
    flattened = []
    stack = [nested_list]

    while stack:
        current = stack.pop()
        if isinstance(current, list):
            stack.extend(reversed(current))
        else:
            flattened.append(current)

    return flattened


from collections.abc import Iterable
from typing import Any, List, Set, Tuple
from collections import deque

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


def flatten_iterative(nested_iterative: Iterable[Any]) -> List[Any]:
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
            f"Expected an iterable, got {type(nested_iterative).__name__}"
        )

    flattened: List[Any] = []
    # Stack stores tuples of (iterator, obj_id) – we track ids only
    stack: deque[Tuple[Any, int]] = deque([(iter(nested_iterative), id(nested_iterative))])
    # Track object ids in the current traversal path to detect cycles
    path: Set[int] = {id(nested_iterative)}

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