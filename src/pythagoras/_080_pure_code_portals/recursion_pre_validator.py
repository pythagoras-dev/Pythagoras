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
    unpacked_kwargs = packed_kwargs.unpack()
    assert param_name in unpacked_kwargs
    fn = fn_addr.get()
    param_value = unpacked_kwargs[param_name]
    assert isinstance(param_value, int)
    assert param_value >= 0
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
    result = []
    for name in args:
        assert isinstance(name, str)
        validator =  ComplexPreValidatorFn(
            _recursion_pre_validator, fixed_kwargs=dict(param_name=name))
        result.append(validator)
    return result