import pytest

from pythagoras import LoggingCodePortal
from pythagoras import _PortalTester
from pythagoras import logging

def demo_fn():
    return 42

def simple_fn(n):
    return n

def test_logging_portal_lazy_binding(tmpdir):
    with _PortalTester(LoggingCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = logging()(demo_fn)
        assert obj.portal is portal
        assert obj._linked_portal is None
        assert obj() == 42
        assert obj._linked_portal is None
        # obj.portal = portal
        # assert obj() == 42
        # assert obj._linked_portal_NEW is portal

        obj = logging()(simple_fn)
        assert obj.portal is portal
        assert obj._linked_portal is None
        assert obj(n=100) == 100
        assert obj._linked_portal is None
        # obj.portal = portal
        # assert obj(n=100) == 100
        # assert obj._linked_portal_NEW is portal


def test_logging_portal_explicit_binding(tmpdir):
    with _PortalTester(LoggingCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = logging(portal=portal)(demo_fn)
        assert obj._linked_portal is portal
        assert obj() == 42
        assert obj._linked_portal is portal

        obj = logging(portal=portal)(simple_fn)
        assert obj._linked_portal is portal
        assert obj(n=100) == 100
        assert obj._linked_portal is portal
