"""Pre-validators that help with recursive pure functions.

This module provides utilities to short-circuit or schedule execution for
recursive calls, e.g., Fibonacci-like functions. The pre-validator returns
either a success flag (skip execution), a call signature to be executed first,
or None to proceed as usual.
"""
from unittest import result

import pythagoras as pth
from .._030_data_portals import *
from .._040_logging_code_portals import *
from .._050_safe_code_portals import *
from .._060_autonomous_code_portals import *
from .._070_protected_code_portals import *
from .pure_core_classes import *


def _recursion_pre_validator(
        packed_kwargs:KwArgs
        , fn_addr:ValueAddr
        , param_name:str
        )-> PureFnCallSignature | ValidationSuccessFlag | None:
    """Pre-validator to aid recursion by ensuring prerequisites are ready.

    For a non-negative integer parameter specified by param_name, this
    validator checks whether smaller sub-problems have already been computed.
    It returns:
    - VALIDATION_SUCCESSFUL if a base case is detected or all smaller results
      are already available; or
    - a PureFnCallSignature for the smallest missing sub-problem to compute
      first; or
    - None to proceed normally.

    Args:
        packed_kwargs: Packed arguments (KwArgs) of the current call.
        fn_addr: ValueAddr pointing to the underlying PureFn.
        param_name: Name of the recursive integer argument to inspect.

    Returns:
        PureFnCallSignature | ValidationSuccessFlag | None: Directive for the
        protected execution pipeline.
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
        return pth.VALIDATION_SUCCESSFUL
    
    # Binary search to find the smallest n where result_addr.ready is not True
    left, right = 2, param_value - 1
    result = pth.VALIDATION_SUCCESSFUL  # Default result if all are ready
    
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
        ) -> list[ComplexPreValidatorFn]:
    """Build pre-validators for one or more recursive parameters.

    Each provided name produces a pre-validator function that uses
    _recursion_pre_validator to ensure prerequisite sub-problems are ready.

    Args:
        *args: One or more names of integer parameters that govern recursion.

    Returns:
        list[ComplexPreValidatorFn]: A list of pre-validators to plug into the
        pure/protected decorator configuration.
    """
    result = []
    for name in args:
        if not isinstance(name, str):
            raise TypeError(f"recursive parameter names must be strings, got {type(name).__name__}")
        validator =  ComplexPreValidatorFn(
            _recursion_pre_validator, fixed_kwargs=dict(param_name=name))
        result.append(validator)
    return result