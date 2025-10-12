"""Pythagoras core convenience namespace.

This module re-exports the most frequently used decorators, classes, and
helpers from the Pythagoras subpackages, providing a compact import surface
for day‑to‑day work. It is safe to use either explicit imports or a star import
from this module depending on your style and needs.

Public API
    ready, get
        Utilities for working with addressable values. "ready(obj)" recursively
        checks that all ValueAddr/HashAddr objects inside a nested structure are
        ready. "get(obj)" deep‑copies a structure and replaces every contained
        address with the concrete value via .get().

    pure, recursive_parameters, PureFn
        Decorator and helpers for pure functions. A pure function is assumed to
        be deterministic and side‑effect free; Pythagoras persistently caches
        its results by call signature and tracks source‑code changes. The
        "recursive_parameters(...)" factory returns pre‑validators used to
        optimize recursive computations.

    autonomous
        Decorator for declaring an autonomous function: implementation must be
        self‑contained (imports done inside the body, no nonlocal/global state
        except built‑ins), with autonomicity validated at decoration and at
        runtime.

    Basic pre‑validators
        Small, composable validators intended to be attached to pure functions,
        for example::

            - unused_cpu(cores: int)
            - unused_ram(Gb: int)
            - installed_packages(*names: str)

        These factories return validator instances (SimplePreValidatorFn) that
        a portal can execute to check whether it should run the user code.

    SwarmingPortal
        Portal enabling asynchronous, distributed ("swarming") execution of
        pure functions across background workers and processes. Execution is
        best‑effort with eventual‑execution semantics.

    get_portal
        Factory for constructing a portal.

Notes
    - Star‑importing from this module will also bring the basic pre‑validators
      into your namespace. Prefer explicit imports if you want a stricter
      namespace.
    - This namespace focuses on high‑impact primitives. For advanced or
      lower‑level APIs, import directly from the corresponding subpackages.
"""

from .._030_data_portals import ready, get
from .._060_autonomous_code_portals import autonomous
from .._070_protected_code_portals.basic_pre_validators import *
from .._080_pure_code_portals import pure, recursive_parameters, PureFn
from .._090_swarming_portals import SwarmingPortal
from .._100_top_level_API import get_portal