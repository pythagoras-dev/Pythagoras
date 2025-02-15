# import sys
#
# from .basic_portal_core_classes import BasicPortal, PortalType
#
# def _most_recently_created_portal(
#         expected_type: PortalType = BasicPortal
#         ) -> PortalType | None:
#     """Get the most recently added portal"""
#     if len(BasicPortal._all_portals) == 0:
#         return None
#     last_key = next(reversed(BasicPortal._all_portals))
#     result = BasicPortal._all_portals[last_key]
#     assert issubclass(expected_type, BasicPortal)
#     assert isinstance(result, expected_type)
#     return result
#
#
# def find_portal_to_use(
#         suggested_portal: PortalType | None = None
#         ,expected_type: PortalType = BasicPortal
#         ) -> PortalType:
#     """Get the portal object from the name or find the best one"""
#     assert issubclass(expected_type, BasicPortal)
#     if suggested_portal is None:
#        suggested_portal = _most_recently_entered_portal()
#     if suggested_portal is None:
#         suggested_portal = _most_recently_created_portal()
#     if suggested_portal is None:
#         # Dirty hack to avoid circular imports
#         suggested_portal = sys.modules["pythagoras"].DefaultLocalPortal()
#     assert isinstance(suggested_portal, expected_type)
#     return suggested_portal
#
#
# def _noncurrent_portals(
#         expected_type: PortalType = BasicPortal) -> list[PortalType]:
#     """Get all portals except the most recently entered one"""
#     current_portal = _most_recently_entered_portal()
#     all_portals = BasicPortal._all_portals
#
#     if current_portal is None:
#         result = [portal for portal in all_portals.values()]
#     else:
#         current_portal_id = id(current_portal)
#         result = [all_portals[portal_id] for portal_id in all_portals
#                   if portal_id != current_portal_id]
#
#     assert issubclass(expected_type, BasicPortal)
#     assert all(isinstance(portal, expected_type) for portal in result)
#
#     return result
#
#
# def _entered_portals(expected_type:PortalType = BasicPortal) -> list[PortalType]:
#     """Get all active portals"""
#     entered_portals = {}
#     for portal in reversed(BasicPortal._entered_portals_stack):
#         entered_portals[id(portal)] = portal
#     result = list(entered_portals.values())
#     if len(result) and expected_type is not None:
#         assert issubclass(expected_type, BasicPortal)
#         assert all(isinstance(portal, expected_type) for portal in result)
#     return result
#
#
# def _most_recently_entered_portal(
#         expected_type: PortalType = BasicPortal
#         ) -> PortalType | None:
#     """Get the current (default) portal object"""
#     if len(BasicPortal._entered_portals_stack) > 0:
#         result = BasicPortal._entered_portals_stack[-1]
#         assert issubclass(expected_type, BasicPortal)
#         assert isinstance(result, expected_type)
#         return result
#     else:
#         return None