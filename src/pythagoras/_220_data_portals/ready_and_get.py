"""
ready_and_get.py – utilities for HashAddr-aware tree traversal
--------------------------------------------------------------

This module offers two convenience helpers that can walk arbitrary
Python object graphs looking for ``HashAddr`` / ``ValueAddr`` objects
defined in *pythagoras* data-portals:

• ready(obj) – depth-first check that *every* address embedded in
  ``obj`` is ``ready`` (i.e. its value can be fetched from at least one
  known portal).

• get(obj)   – deep-copy of ``obj`` where every address is replaced by
  its resolved value (via ``.get()``).  Container topology and identity
  are preserved and cycles are handled correctly.

The functions leverage mixinforge utility functions for traversal,
supporting a wide range of container types including custom Mapping,
Sequence, and objects with __dict__ or __slots__.
"""
from __future__ import annotations

from typing import Any

from mixinforge.utility_functions import (
    find_instances_inside_composite_object,
    transform_instances_inside_composite_object,
)

from .data_portal_core_classes import HashAddr


def ready(obj: Any) -> bool:
    """Recursively verify that **all** HashAddr objects inside *obj* are ready."""
    for addr in find_instances_inside_composite_object(obj, HashAddr):
        if not addr.ready:
            return False
    return True


def get(obj: Any) -> Any:
    """Return a deep copy of *obj* with every HashAddr replaced by its value."""
    return transform_instances_inside_composite_object(
        obj,
        HashAddr,
        lambda addr: addr.get()
    )