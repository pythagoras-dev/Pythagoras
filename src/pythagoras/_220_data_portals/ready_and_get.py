"""Utilities for HashAddr-aware object graph traversal.

This module provides convenience helpers for working with object graphs
that contain HashAddr/ValueAddr instances:

- ready(obj): Check if all addresses in a structure are retrievable
- get(obj): Deep-copy with all addresses replaced by their values

The functions support arbitrary container types including Mapping,
Sequence, and objects with __dict__ or __slots__. Cycles are handled
correctly.
"""
from __future__ import annotations

from typing import Any

from mixinforge.utility_functions import (
    find_instances_inside_composite_object,
    transform_instances_inside_composite_object,
)

from .data_portal_core_classes import HashAddr


def ready(obj: Any) -> bool:
    """Check if all HashAddr instances in an object graph are retrievable.

    Args:
        obj: Object structure to check, may contain nested HashAddr instances.

    Returns:
        True if every HashAddr in obj has its value available in at least
        one known portal, False otherwise.
    """
    for addr in find_instances_inside_composite_object(obj, HashAddr):
        if not addr.ready:
            return False
    return True


def get(obj: Any) -> Any:
    """Deep-copy an object graph, resolving all HashAddr instances to values.

    Args:
        obj: Object structure to copy, may contain nested HashAddr instances.

    Returns:
        A deep copy of obj where every HashAddr is replaced by the value
        it references. Container topology and object identity are preserved.
    """
    return transform_instances_inside_composite_object(
        obj,
        HashAddr,
        lambda addr: addr.get()
    )