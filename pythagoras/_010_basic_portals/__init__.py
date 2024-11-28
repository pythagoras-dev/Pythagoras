"""Foundational classes and utilities to work with Pythagoras portals.

In a Pythagoras-based application, a portal is the application's 'window'
into the non-ephemeral world outside the current application execution
session. It's a connector that enables a link between a runtime-only
ephemeral state and a persistent state that can be saved and loaded
across multiple runs of the application, and across multiple computers.

A Pythagoras-based application can have multiple portals.
There is usually a current (default) portal, accessible via
get_current_portal().

BasicPortal is the base class for all portal objects. It provides core
functionality for managing the portal stack and for accessing the current
portal. The class is not intended to be used directly. Instead, it should
be subclassed to provide additional functionality.

BasicPortal's subclasses are expected to provide access to
the portal's data and to manage the portal's state.
This access is supposed to be offered by using PersiDict
objects, which are persistent dictionaries: they have Dict-like interface
while allowing to work with non-ephemeral storage.
PersiDict-s are heavily used in Pythagoras.

PortalAwareClass is a base class for classes that use a portal object
as a context that helps to manage the class's state and behaviour.
PortalAwareClass is also not intended to be used directly. It should
be subclassed to provide additional functionality.
"""

from .exceptions import NotAllowedError
from .foundation import BasicPortal
from .portal_aware_classes import PortalAwareClass
from .portal_tester import _PortalTester

