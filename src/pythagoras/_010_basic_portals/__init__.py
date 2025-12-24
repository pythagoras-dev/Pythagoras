"""Foundational classes and utilities to work with Pythagoras portals.

In a Pythagoras-based application, a portal is the application's 'window'
into the non-ephemeral world outside the current application execution
session. It serves as a connector linking runtime-only ephemeral state
with persistent state that can be saved and loaded across multiple
application runs and computers.

Beyond being a 'window', a portal also provides various supporting services
that help manage the application's state and behavior.

BasicPortal is the base class for all portal objects. It is not intended
to be used directly; instead, it should be subclassed to provide
concrete functionality.

BasicPortal's subclasses are expected to provide access to the portal's data
and manage its state. This access is typically offered via PersiDict objects—
persistent dictionaries that expose a Dict-like interface while backed by
non-ephemeral storage. PersiDicts are heavily used throughout Pythagoras.

PortalAwareClass is a base class for classes that use a portal object
as a context for managing state and behavior. Like BasicPortal,
PortalAwareClass is not intended for direct use and should be subclassed.

A Pythagoras-based application can have multiple portals. A portal becomes
active when used within a `with` statement. The most recent portal in the
stack of active portals is considered the current active portal, which can
be accessed via the `get_current_active_portal()` function. This portal
is used by code executed inside the `with` block.

If PortalAwareClass-based objects are accessed by the code, they will use
the current active portal unless they were explicitly linked to a specific
portal at creation time. If there are no active portals when a
PortalAwareClass-based object needs one, a default portal will be
instantiated and activated automatically.


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