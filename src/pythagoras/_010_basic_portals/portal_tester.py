from __future__ import annotations
from .basic_portal_core_classes import (
    BasicPortal, PortalType, _clear_all_portals)


class _PortalTester:
    """A context manager for testing portal objects.

    The class is used to test the portal objects.
    It ensures that all portal objects are properly initialized and cleared
    between tests. This class is not supposed to be used in application code,
    it only exists for unit tests.
    """
    _current_instance:_PortalTester|None = None
    _portal:BasicPortal|None = None

    def __init__(self,portal_class:PortalType|None = None,*args,**kwargs):

        if _PortalTester._current_instance is not None:
            raise Exception("_PortalTester can't be nested")
        _PortalTester._current_instance = self

        if portal_class is not None:
            assert issubclass(portal_class, BasicPortal)
        self.portal_class = portal_class
        self.args = args
        self.kwargs = kwargs


    @property
    def portal(self) -> BasicPortal|None:
        """The portal object being tested."""
        return self._portal


    def __enter__(self):
        if (_PortalTester._current_instance is not None
                and _PortalTester._current_instance is not self):
            raise Exception("_PortalTester can't be nested")
        _PortalTester._current_instance = self

        _clear_all_portals()

        if self.portal_class is not None:
            self._portal = self.portal_class(*self.args,**self.kwargs)
            self.portal.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self.portal_class is not None:
            self.portal.__exit__(exc_type, exc_val, exc_tb)
            self._portal = None

        _clear_all_portals()

        _PortalTester._current_instance = None