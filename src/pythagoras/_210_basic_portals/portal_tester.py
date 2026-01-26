"""Context manager for portal unit testing.

Provides `_PortalTester`, which ensures proper portal initialization
and cleanup between tests. Not intended for application code.
"""

from __future__ import annotations
from .basic_portal_core_classes import (
    BasicPortal, PortalType, _clear_all_portals)
from .._110_supporting_utilities import get_long_infoname


class _PortalTester:
    """A context manager for testing portal objects.

    Ensures that all portal objects are properly initialized and cleared
    between tests. Automatically clears the global portal registry on entry
    and exit. Intended for internal unit tests only, not for application code.

    Example:
        >>> with _PortalTester(BasicPortal) as tester:
        ...     assert tester.portal is not None
        ...     # Test portal functionality
    """
    _current_instance:_PortalTester|None = None
    _portal:BasicPortal|None = None

    def __init__(self, portal_class: PortalType | None = None, *args, **kwargs):
        """Initialize the portal tester.

        Args:
            portal_class: Portal class to instantiate and test, or None.
            *args: Positional arguments for portal constructor.
            **kwargs: Keyword arguments for portal constructor.

        Raises:
            Exception: If another _PortalTester instance is already active.
            TypeError: If portal_class is not a subclass of BasicPortal.
        """
        if _PortalTester._current_instance is not None:
            raise Exception("_PortalTester can't be nested")
        _PortalTester._current_instance = self

        if portal_class is not None:
            if not issubclass(portal_class, BasicPortal):
                raise TypeError(
                    f"portal_class must be a subclass of BasicPortal, "
                    f"got {get_long_infoname(portal_class)}")
        self.portal_class = portal_class
        self.args = args
        self.kwargs = kwargs


    @property
    def portal(self) -> BasicPortal | None:
        """The portal object being tested, or None if no portal was created."""
        return self._portal

    def __enter__(self):
        """Enter the portal testing context.

        Clears all existing portals and creates a new portal if specified.

        Returns:
            The _PortalTester instance.

        Raises:
            Exception: If another _PortalTester is already active.
        """
        if (_PortalTester._current_instance is not None
                and _PortalTester._current_instance is not self):
            raise Exception("_PortalTester can't be nested")
        _PortalTester._current_instance = self

        _clear_all_portals()

        if self.portal_class is not None:
            self._portal = self.portal_class(*self.args, **self.kwargs)
            self.portal.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the portal testing context and clean up.

        Args:
            exc_type: Exception type if an exception occurred, None otherwise.
            exc_val: Exception value if an exception occurred, None otherwise.
            exc_tb: Exception traceback if an exception occurred, None otherwise.
        """
        if self.portal_class is not None:
            self.portal.__exit__(exc_type, exc_val, exc_tb)
            self._portal = None

        _clear_all_portals()

        _PortalTester._current_instance = None