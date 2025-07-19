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
    for n in range(2, param_value): #TODO: optimize this
        unpacked_kwargs[param_name] = n
        result_addr = pth.PureFnExecutionResultAddr(
            fn=fn, arguments = unpacked_kwargs)
        if not result_addr.ready:
            return result_addr.call_signature
    return pth.VALIDATION_SUCCESSFUL


def recursive_parameter(param_name:str):
    return ComplexPreValidatorFn(
        _recursion_pre_validator
        , fixed_kwargs=dict(param_name=param_name))

