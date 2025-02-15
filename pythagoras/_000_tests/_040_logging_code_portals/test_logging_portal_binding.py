import pytest

from pythagoras import LoggingCodePortal
from pythagoras import _PortalTester
from pythagoras import LoggingFn, logging

def demo_fn():
    return 42

def simple_fn(n):
    return n

def test_logging_portal_lazy_binding(tmpdir):
    with _PortalTester(LoggingCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = logging()(demo_fn)
        assert obj._portal is None
        assert obj() == 42
        assert obj._portal is portal

        obj = logging()(simple_fn)
        assert obj._portal is None
        assert obj(n=100) == 100
        assert obj._portal is portal


def test_logging_portal_explicit_binding(tmpdir):
    with _PortalTester(LoggingCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = logging(portal=portal)(demo_fn)
        assert obj._portal is portal
        assert obj() == 42
        assert obj._portal is portal

        obj = logging(portal=portal)(simple_fn)
        assert obj._portal is portal
        assert obj(n=100) == 100
        assert obj._portal is portal


def test_logging_portal_set_portal(tmpdir):
    with _PortalTester(LoggingCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = logging()(demo_fn)
        assert obj._portal is None
        obj.portal = portal
        assert obj._portal is portal
        assert obj() == 42
        assert obj._portal is portal

        obj.portal = portal
        assert obj._portal is portal
        assert obj.portal is portal
        assert obj._portal is portal

        obj.portal = portal
        assert obj._portal is portal
        assert obj.portal is portal
        assert obj._portal is portal

        new_portal = LoggingCodePortal()
        with pytest.raises(ValueError):
            obj.portal = new_portal