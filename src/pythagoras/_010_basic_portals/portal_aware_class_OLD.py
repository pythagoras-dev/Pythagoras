from __future__ import annotations

import sys
from abc import ABCMeta, abstractmethod
from copy import copy

from .basic_portal_class_OLD import BasicPortal, PortalType


class PortalAwareMetaclass(ABCMeta):
    """Ensures method .register_in_portal() is always called after constructor.
    """
    def __call__(self, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        instance.register_in_portal()
        return instance


class PortalAwareClass(metaclass = PortalAwareMetaclass):
    """A base class for objects that need to access a portal.

    The class enables functionality for saving and loading its objects.
    When a portal-aware object is saved (pickled), the portal data is not saved,
    and the object is pickled as if it were a regular object.
    After the object is unpickled, the portal is restored to the current portal.

    The "current" portal is the innermost portal
    in the stack of portal "with" statements. It means that
    a portal-aware object can only be unpickled from within a portal context.

    A portal-aware object accepts a portal as an input parameter
    for its constructor. It also supports late portal binding: it
    can be created with `portal=None`, and its portal will be set later
    to the current portal.
    """

    _portal: BasicPortal|None

    def __init__(self, portal:BasicPortal|None=None):
        assert portal is None or isinstance(portal, BasicPortal)
        self._portal = portal


    def register_in_portal(self):
        pass


    @property
    def portal(self) -> BasicPortal:
        if not hasattr(self, "_linked_portal"):
            self._portal = None
        return self._portal


    @portal.setter
    def portal(self, value: BasicPortal|None) -> None:
        """Set the portal to the given one."""
        assert isinstance(value, BasicPortal)
        if (hasattr(self, "_linked_portal")
                and self._portal is not None
                and self._portal != value):
            raise ValueError("You can set the portal only once.")
        self._portal = value
        self.register_in_portal()


    @property
    def finally_bound_portal(self) -> BasicPortal:
        """Return the portal to use for the object.

        If the portal is not set, return the current portal.
        If the portal is set, return it.
        """
        if self.portal is None:
            self.portal = find_portal_to_use()
        return self.portal


    def _portal_typed(self
            , expected_type: PortalType = BasicPortal
            ) -> PortalType:
        assert issubclass(expected_type, BasicPortal)
        assert isinstance(self._portal, expected_type) or self._portal is None
        return self._portal


    @abstractmethod
    def __getstate__(self):
        """This method is called when the object is pickled.

        Make sure NOT to include portal info the object's state
        while pickling it.
        """
        raise NotImplementedError(
            "PortalAwareClass objects must have custom __getstate__() method, "
            + "otherwise they are not picklable.")


    @abstractmethod
    def __setstate__(self, state):
        """This method is called when the object is unpickled.

        """
        self._portal = None


    def __copy__(self):
        #TODO: check the logic of this method
        result = self.__new__(type(self))
        result.__setstate__(self.__getstate__())
        assert not hasattr(result, "_linked_portal") or result._portal is None
        result._portal = None
        return result


    def __matmul__(self, portal: BasicPortal) -> PortalAwareClass:
        """Return a copy of self with the portal set to the given one."""
        with portal:
            result = copy(self)
        result.portal = portal
        return result


    def _invalidate_cache(self):
        pass


def _most_recently_created_portal(
        expected_type: PortalType = BasicPortal
        ) -> PortalType | None:
    """Get the most recently added portal"""
    if len(BasicPortal._all_portals) == 0:
        return None
    last_key = next(reversed(BasicPortal._all_portals))
    result = BasicPortal._all_portals[last_key]
    assert issubclass(expected_type, BasicPortal)
    assert isinstance(result, expected_type)
    return result


def find_portal_to_use(
        suggested_portal: PortalType | None = None
        ,expected_type: PortalType = BasicPortal
        ) -> PortalType:
    """Get the portal object from the name or find the best one"""
    assert issubclass(expected_type, BasicPortal)
    if suggested_portal is None:
       suggested_portal = _most_recently_entered_portal()
    if suggested_portal is None:
        suggested_portal = _most_recently_created_portal()
    if suggested_portal is None:
        # Dirty hack to avoid circular imports
        suggested_portal = sys.modules["pythagoras"].defaul_portal()
    assert isinstance(suggested_portal, expected_type)
    return suggested_portal


def _noncurrent_portals(
        expected_type: PortalType = BasicPortal) -> list[PortalType]:
    """Get all portals except the most recently entered one"""
    current_portal = _most_recently_entered_portal()
    all_portals = BasicPortal._all_portals

    if current_portal is None:
        result = [portal for portal in all_portals.values()]
    else:
        current_portal_id = id(current_portal)
        result = [all_portals[portal_id] for portal_id in all_portals
                  if portal_id != current_portal_id]

    assert issubclass(expected_type, BasicPortal)
    assert all(isinstance(portal, expected_type) for portal in result)

    return result


def _entered_portals(expected_type:PortalType = BasicPortal) -> list[PortalType]:
    """Get all active portals"""
    entered_portals = {}
    for portal in reversed(BasicPortal._entered_portals_stack):
        entered_portals[id(portal)] = portal
    result = list(entered_portals.values())
    if len(result) and expected_type is not None:
        assert issubclass(expected_type, BasicPortal)
        assert all(isinstance(portal, expected_type) for portal in result)
    return result


def _most_recently_entered_portal(
        expected_type: PortalType = BasicPortal
        ) -> PortalType | None:
    """Get the current (default) portal object"""
    if len(BasicPortal._entered_portals_stack) > 0:
        result = BasicPortal._entered_portals_stack[-1]
        assert issubclass(expected_type, BasicPortal)
        assert isinstance(result, expected_type)
        return result
    else:
        return None