"""Tests for _PortalStack class.

Tests the stack data structure that manages active portals for context
manager support, including re-entrancy counting.
"""
import pytest
from unittest.mock import MagicMock

from pythagoras._210_basic_portals.basic_portal_core_classes import (
    _PortalStack, MAX_NESTED_PORTALS
)


def test_empty_stack_properties():
    """Verify empty stack reports correct state."""
    stack = _PortalStack()

    assert stack.is_empty()
    assert stack.depth() == 0
    assert stack.unique_count() == 0
    assert stack.peek() is None
    assert stack.as_set() == set()


def test_push_adds_portal_to_stack():
    """Verify push makes portal accessible via peek and updates counts."""
    stack = _PortalStack()
    portal = MagicMock()

    stack.push(portal)

    assert not stack.is_empty()
    assert stack.peek() is portal
    assert stack.depth() == 1
    assert stack.unique_count() == 1
    assert stack.contains(portal)


def test_pop_removes_portal_from_stack():
    """Verify pop returns stack to empty state."""
    stack = _PortalStack()
    portal = MagicMock()
    stack.push(portal)

    stack.pop(portal)

    assert stack.is_empty()
    assert stack.peek() is None
    assert stack.depth() == 0
    assert not stack.contains(portal)


def test_stack_follows_lifo_order():
    """Verify portals are popped in reverse order of pushing."""
    stack = _PortalStack()
    portal1, portal2, portal3 = MagicMock(), MagicMock(), MagicMock()

    stack.push(portal1)
    stack.push(portal2)
    stack.push(portal3)

    assert stack.peek() is portal3
    assert stack.depth() == 3
    assert stack.unique_count() == 3

    stack.pop(portal3)
    assert stack.peek() is portal2

    stack.pop(portal2)
    assert stack.peek() is portal1


def test_reentrant_push_increments_counter():
    """Verify pushing same portal multiple times increments depth but not unique count."""
    stack = _PortalStack()
    portal = MagicMock()

    stack.push(portal)
    stack.push(portal)
    stack.push(portal)

    assert stack.depth() == 3
    assert stack.unique_count() == 1
    assert stack.peek() is portal


def test_reentrant_pop_decrements_counter():
    """Verify popping re-entrant portal decrements counter before removing."""
    stack = _PortalStack()
    portal = MagicMock()
    stack.push(portal)
    stack.push(portal)
    stack.push(portal)

    stack.pop(portal)
    assert stack.depth() == 2
    assert stack.peek() is portal

    stack.pop(portal)
    assert stack.depth() == 1

    stack.pop(portal)
    assert stack.is_empty()


def test_mixed_reentrant_and_different_portals():
    """Verify mixed re-entrant and different portals work correctly."""
    stack = _PortalStack()
    portal1, portal2 = MagicMock(), MagicMock()

    stack.push(portal1)
    stack.push(portal1)  # re-entrant
    stack.push(portal2)
    stack.push(portal2)  # re-entrant

    assert stack.depth() == 4
    assert stack.unique_count() == 2

    stack.pop(portal2)
    assert stack.peek() is portal2

    stack.pop(portal2)
    assert stack.peek() is portal1


def test_contains_finds_portal_anywhere_in_stack():
    """Verify contains returns True for any portal in stack, not just top."""
    stack = _PortalStack()
    portal1, portal2, portal3 = MagicMock(), MagicMock(), MagicMock()
    other_portal = MagicMock()

    stack.push(portal1)
    stack.push(portal2)
    stack.push(portal3)

    assert stack.contains(portal1)
    assert stack.contains(portal2)
    assert stack.contains(portal3)
    assert not stack.contains(other_portal)


def test_is_top_only_for_top_portal():
    """Verify is_top returns True only for the topmost portal."""
    stack = _PortalStack()
    portal1, portal2 = MagicMock(), MagicMock()

    stack.push(portal1)
    stack.push(portal2)

    assert stack.is_top(portal2)
    assert not stack.is_top(portal1)


def test_as_set_returns_unique_portals():
    """Verify as_set returns unique portals regardless of re-entrancy."""
    stack = _PortalStack()
    portal1, portal2 = MagicMock(), MagicMock()

    stack.push(portal1)
    stack.push(portal1)  # re-entrant
    stack.push(portal2)

    result = stack.as_set()

    assert result == {portal1, portal2}


def test_clear_removes_all_portals():
    """Verify clear empties the stack completely."""
    stack = _PortalStack()
    portal1, portal2 = MagicMock(), MagicMock()
    stack.push(portal1)
    stack.push(portal1)
    stack.push(portal2)

    stack.clear()

    assert stack.is_empty()
    assert stack.depth() == 0
    assert stack.peek() is None


def test_pop_empty_stack_raises():
    """Verify popping from empty stack raises RuntimeError."""
    stack = _PortalStack()
    portal = MagicMock()

    with pytest.raises(RuntimeError):
        stack.pop(portal)


def test_pop_wrong_portal_raises():
    """Verify popping wrong portal raises RuntimeError."""
    stack = _PortalStack()
    portal1, portal2 = MagicMock(), MagicMock()
    stack.push(portal1)

    with pytest.raises(RuntimeError):
        stack.pop(portal2)


def test_max_nested_portals_limit():
    """Verify stack enforces MAX_NESTED_PORTALS limit."""
    stack = _PortalStack()
    portals = [MagicMock() for _ in range(MAX_NESTED_PORTALS)]

    for p in portals:
        stack.push(p)

    assert stack.depth() == MAX_NESTED_PORTALS

    with pytest.raises(RuntimeError):
        stack.push(MagicMock())


def test_max_nested_with_reentrant_portal():
    """Verify MAX_NESTED_PORTALS applies to total depth including re-entrancy."""
    stack = _PortalStack()
    portal = MagicMock()

    for _ in range(MAX_NESTED_PORTALS):
        stack.push(portal)

    assert stack.depth() == MAX_NESTED_PORTALS
    assert stack.unique_count() == 1

    with pytest.raises(RuntimeError):
        stack.push(portal)
