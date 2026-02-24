"""Requirements that help with recursive pure functions.

This module provides utilities to short-circuit or schedule execution for
recursive calls, e.g., Fibonacci-like functions. The requirement returns
either NO_OBJECTIONS (skip execution), a call signature to be executed first,
or None to proceed as usual.
"""

import pythagoras as pth
from .._220_data_portals import *
from .._320_logging_code_portals import *
from .._330_safe_code_portals import *
from .._340_autonomous_code_portals import *
from .._350_guarded_code_portals import *
from .pure_core_classes import *


def _recursion_requirement(
        packed_kwargs:KwArgs
        , fn_addr:ValueAddr
        , param_name:str
        )-> PureFnCallSignature | NoObjectionsFlag | None:
    """Requirement to aid recursion by ensuring prerequisites are ready.

    For a non-negative integer parameter specified by param_name, this
    requirement checks whether smaller sub-problems have already been computed.
    It returns:
    - NO_OBJECTIONS if a base case is detected or all smaller results
      are already available; or
    - a PureFnCallSignature for the smallest missing sub-problem to compute
      first; or
    - None to proceed normally.

    Args:
        packed_kwargs: Packed arguments (KwArgs) of the current call.
        fn_addr: ValueAddr pointing to the underlying PureFn.
        param_name: Name of the recursive integer argument to inspect.

    Returns:
        PureFnCallSignature | NoObjectionsFlag | None: Directive for the
        guarded execution pipeline.
    """
    unpacked_kwargs = packed_kwargs.unpack()
    if param_name not in unpacked_kwargs:
        raise KeyError(f"Missing required parameter '{param_name}' in kwargs")
    fn = fn_addr.get()
    param_value = unpacked_kwargs[param_name]
    if not isinstance(param_value, int):
        raise TypeError(f"Parameter '{param_name}' must be int, got {type(param_value).__name__}")
    if param_value < 0:
        raise ValueError(f"Parameter '{param_name}' must be non-negative, got {param_value}")
    if param_value in {0,1}:
        return pth.NO_OBJECTIONS

    # Binary search to find the smallest n where result_addr.ready is not True
    left, right = 2, param_value - 1
    result = pth.NO_OBJECTIONS  # Default result if all are ready

    while left <= right:
        mid = (left + right) // 2
        unpacked_kwargs[param_name] = mid
        result_addr = pth.PureFnExecutionResultAddr(
            fn=fn, arguments=unpacked_kwargs)

        if not result_addr.ready:
            # Found a value where result is not ready
            result = result_addr.call_signature
            # Continue searching in the left half to find the smallest such value
            right = mid - 1
        else:
            # Result is ready, search in the right half
            left = mid + 1


    return result


def recursive_parameters(
        *args
        ) -> list[ComplexRequirementFn]:
    """Build requirements for one or more recursive parameters.

    Each provided name produces a requirement function that uses
    _recursion_requirement to ensure prerequisite sub-problems are ready.

    Args:
        *args: One or more names of integer parameters that govern recursion.

    Returns:
        list[ComplexRequirementFn]: A list of requirements to plug into the
        pure/guarded decorator configuration.
    """
    result = []
    for name in args:
        if not isinstance(name, str):
            raise TypeError(f"recursive parameter names must be strings, got {type(name).__name__}")
        requirement = ComplexRequirementFn(
            _recursion_requirement, fixed_kwargs=dict(param_name=name))
        result.append(requirement)
    return result
