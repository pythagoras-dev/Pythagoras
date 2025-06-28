# import pytest
#
# from pythagoras import OrdinaryCodePortal
# from pythagoras import _PortalTester
# from pythagoras import ordinary
#
# def demo_fn():
#     return 42
#
# def simple_fn(n):
#     return n
#
# def test_ordinary_portal_lazy_binding(tmpdir):
#     with _PortalTester(OrdinaryCodePortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         obj = ordinary()(demo_fn)
#         assert obj._portal is None
#         assert obj() == 42
#         assert obj._portal is portal
#
#         obj = ordinary()(simple_fn)
#         assert obj._portal is None
#         assert obj(n=100) == 100
#         assert obj._portal is portal
#
#
# def test_ordinary_portal_explicit_binding(tmpdir):
#     with _PortalTester(OrdinaryCodePortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         obj = ordinary(portal)(demo_fn)
#         assert obj._portal is portal
#         assert obj() == 42
#         assert obj._portal is portal
#
#         obj = ordinary(portal)(simple_fn)
#         assert obj._portal is portal
#         assert obj(n=100) == 100
#         assert obj._portal is portal
#
#
# def test_ordinary_portal_set_portal(tmpdir):
#     with _PortalTester(OrdinaryCodePortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         obj = ordinary()(demo_fn)
#         assert obj._portal is None
#         obj.portal = portal
#         assert obj._portal is portal
#         assert obj() == 42
#         assert obj._portal is portal
#
#         obj.portal = portal
#         assert obj._portal is portal
#         assert obj.portal is portal
#         assert obj._portal is portal
#
#         obj.portal = portal
#         assert obj._portal is portal
#         assert obj.portal is portal
#         assert obj._portal is portal
#
#         new_portal = OrdinaryCodePortal()
#         with pytest.raises(ValueError):
#             obj.portal = new_portal