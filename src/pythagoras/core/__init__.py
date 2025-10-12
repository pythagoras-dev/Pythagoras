"""Core convenience namespace for Pythagoras.

This module aggregates the most frequently used decorators and helpers into a
single import location, so you can write concise imports like::

    from pythagoras.core import *

or explicitly import only what you need::

    from pythagoras.core import pure, autonomous, ready, get

The symbols re-exported here come from specialized subpackages and are commonly
used together when building Pythagoras-based workflows.

Exports
-------
- ready, get:
  Utilities to work with values referenced through addresses.
  - ready(obj): Recursively checks that all addresses within a nested
    structure are ready to be fetched.
  - get(obj): Deep-copies a structure, replacing every address with
    the actual stored value via .get().

- autonomous:
  A decorator that marks a function as autonomous and enforces autonomicity
  constraints both at decoration time and at runtime.

- Basic pre-validators:
  A set of small, composable validators intended to be attached to protected
  portals before executing user code (e.g., unused_cpu, unused_ram,
  installed_packages, etc.). These are star-imported for convenience.

- pure, recursive_parameters, PureFn:
  Tools for declaring and working with pure functions whose results are
  persistently cached. The recursive_parameters pre-validator helps optimize
  execution of the recursive code.

- SwarmingPortal:
  Infrastructure for asynchronous, distributed execution ("swarming") of
  pure functions in a cluster or cloud environment.

- get_portal:
  Factory for obtaining a configured portal instance to coordinate execution
  and storage.

Usage
-----
Typical usage patterns include attaching validators pure functions,
leveraging ready/get to materialize data structures, and using
autonomous/pure decorators to control execution guarantees.

Notes
-----
- Star-importing also brings in basic pre-validators into your namespace. If
  you prefer a stricter namespace, import names explicitly instead of using
  a wildcard import.
- The re-export list is intentionally small and focused on high-impact, common
  primitives. For advanced usage, import directly from the corresponding
  subpackages.
"""

from .._030_data_portals import ready, get
from .._060_autonomous_code_portals import autonomous
from .._070_protected_code_portals.basic_pre_validators import *
from .._080_pure_code_portals import pure, recursive_parameters, PureFn
from .._090_swarming_portals import SwarmingPortal
from .._100_top_level_API import get_portal