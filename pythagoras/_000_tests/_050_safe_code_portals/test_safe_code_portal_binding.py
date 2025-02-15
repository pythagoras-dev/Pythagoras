import pytest

from pythagoras import SafeCodePortal
from pythagoras import _PortalTester
from pythagoras import SafeFn, safe

def demo_fn():
    return 42

def simple_fn(n):
    return n

def test_safe_code_portal_lazy_binding(tmpdir):
    with _PortalTester(SafeCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = safe()(demo_fn)
        assert obj._portal is None
        assert obj() == 42
        assert obj._portal is portal

        obj = safe()(simple_fn)
        assert obj._portal is None
        assert obj(n=100) == 100
        assert obj._portal is portal


def test_safe_code_portal_explicit_binding(tmpdir):
    with _PortalTester(SafeCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = safe(portal=portal)(demo_fn)
        assert obj._portal is portal
        assert obj() == 42
        assert obj._portal is portal

        obj = safe(portal=portal)(simple_fn)
        assert obj._portal is portal
        assert obj(n=100) == 100
        assert obj._portal is portal


# def test_safe_code_portal_set_portal(tmpdir):
#     with _PortalTester(SafeCodePortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         obj = safe()(demo_fn)
#         assert obj._portal is None
#         obj.set_portal(portal)
#         assert obj._portal is portal
#         assert obj() == 42
#         assert obj._portal is portal
#
#         obj.set_portal(portal)
#         assert obj._portal is portal
#         assert obj.portal is portal
#         assert obj._portal is portal
#
#         obj.set_portal(portal)
#         assert obj._portal is portal
#         assert obj.portal is portal
#         assert obj._portal is portal
#
#         new_portal = SafeCodePortal()
#         with pytest.raises(ValueError):
#             obj.set_portal(new_portal)