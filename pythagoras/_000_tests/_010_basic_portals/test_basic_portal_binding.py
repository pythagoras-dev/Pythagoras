import pytest

from pythagoras import BasicPortal
from pythagoras import _PortalTester
from pythagoras import PortalAwareClass

# def test_basic_portal_lazy_binding(tmpdir):
#     with _PortalTester(BasicPortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         obj = PortalAwareClass()
#         assert obj._portal is None
#         assert obj.portal is portal
#         assert obj._portal is portal

#
# def test_basic_portal_explicit_binding(tmpdir):
#     with _PortalTester(BasicPortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         obj = PortalAwareClass(portal)
#         assert obj._portal is portal
#         assert obj.portal is portal
#         assert obj._portal is portal
#
#
# def test_basic_portal_set_portal(tmpdir):
#     with _PortalTester(BasicPortal, root_dict = tmpdir) as t:
#         portal = t.portal
#         obj = PortalAwareClass()
#         obj.portal = portal
#         assert obj._portal is portal
#         assert obj.portal is portal
#         assert obj._portal is portal
#         obj.portal = portal
#         assert obj._portal is portal
#         assert obj.portal is portal
#         assert obj._portal is portal
#
#         new_portal = BasicPortal()
#         with pytest.raises(ValueError):
#             obj.portal = new_portal