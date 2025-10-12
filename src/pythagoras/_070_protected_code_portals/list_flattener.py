from typing import List, Any


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