"""Classes and utilities for swarming execution in Pythagoras.

Swarming is an asynchronous execution model where pure-function calls are
enqueued and executed by available workers across processes or machines.
The model guarantees eventual execution (at least once) but not timing,
worker assignment, or single execution.

Main exports:
- SwarmingPortal: Portal for distributed swarming execution of pure functions.
- DescendantProcessInfo: Tracks descendant processes spawned by a swarming portal.
"""

from .system_processes_info_getters import *
from .swarming_portals import *
