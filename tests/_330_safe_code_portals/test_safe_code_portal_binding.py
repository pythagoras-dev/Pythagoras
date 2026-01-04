from pythagoras import SafeCodePortal
from pythagoras import _PortalTester
from pythagoras import safe

def demo_fn():
    return 42

def simple_fn(n):
    return n

def test_safe_code_portal_lazy_binding(tmpdir):
    with _PortalTester(SafeCodePortal, root_dict = tmpdir) as t:
        portal = t.portal
        obj = safe()(demo_fn)
        assert obj() == 42
        assert obj.linked_portal is None
        assert obj.portal is portal

        obj = safe()(simple_fn)
        assert obj(n=100) == 100
        assert obj.linked_portal is None
        assert obj.portal is portal


def test_safe_code_portal_explicit_binding(tmpdir):
    with _PortalTester(SafeCodePortal, root_dict = tmpdir) as t:
        portal = t.portal

        obj = safe(portal=portal)(demo_fn)
        assert obj.portal is portal
        assert obj() == 42
        assert obj.linked_portal is portal
        assert obj.portal is portal

        obj = safe(portal=portal)(simple_fn)
        assert obj.portal is portal
        assert obj(n=100) == 100
        assert obj.linked_portal is portal
        assert obj.portal is portal

