"""Foundational classes and utilities to work with Pythagoras portals.

In a Pythagoras-based application, a portal is the application's 'window'
into the non-ephemeral world outside the current application execution
session. It's a connector that enables a link between a runtime-only
ephemeral state and a persistent state that can be saved and loaded
across multiple runs of the application, and across multiple computers.

However, being a 'window' is not the only thing a portal does. It also
provides various supporting services that help manage the application's
state and behavior.

BasicPortal is a base class for all portal objects.
The class is not intended to be used directly.
Instead, it should be subclassed to provide additional functionality.

BasicPortal's subclasses are expected to provide access to
the portal's data and to manage the portal's state.
This access is supposed to be offered by using PersiDict
objects, which are persistent dictionaries: they have Dict-like interface
while allowing to work with non-ephemeral storage.
PersiDict-s are heavily used in Pythagoras.

PortalAwareClass is a base class for classes that use a portal object
as a context that helps to manage the class' state and behavior.
PortalAwareClass is also not intended to be used directly. It should
be subclassed to provide additional functionality.

A Pythagoras-based application can have multiple portals.
A portal becomes active when it is used with a with-statement.
The most recent portal in a stack of active portals is considered
the current active portal. get_current_active_portal() function allows to access it.
It is the portal used by code that is executed inside the with block.
If there are PortalAwareClass-based objects accessed by the code,
they will use the current active portal, unless they were explicitly linked
to a specific portal at the time of creation.
If there are no active portals at the time when a PortalAwareClass-based
object needs one it, a default portal will be instantiated in the system and activated.


Important Notes
---------------
**Thread Safety**: Work with portals is NOT thread-safe. Portal management uses
global state that is not protected by locks. All portal operations
must be performed from a single thread.
"""

from .guarded_init_metaclass import *
from .basic_portal_core_classes import *
from .default_portal_base_dir import get_default_portal_base_dir
from .portal_tester import _PortalTester