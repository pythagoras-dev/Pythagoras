from pythagoras._060_autonomous_code_portals import AutonomousFn, autonomous
from .OK_const import OK
import pythagoras as pth


def free_ram_bytes(packed_kwargs, fn_addr, required_memory):
    import psutil
    mem_info = psutil.virtual_memory()
    if mem_info.available >= required_memory:
        return pth.OK


def RAM_K(limit:int) -> AutonomousFn:
    global free_ram_bytes
    if not isinstance(free_ram_bytes, AutonomousFn):
        free_ram_bytes = autonomous()(free_ram_bytes)
    limit = int(limit/1024)
    assert limit > 0
    return free_ram_bytes.fix_kwargs(required_memory = limit)


def RAM_M(limit:int) -> AutonomousFn:
    limit = int(limit/1024)
    return RAM_K(limit)


def RAM_G(limit:int) -> AutonomousFn:
    limit = int(limit/1024)
    return RAM_M(limit)


def RAM_T(limit:int) -> AutonomousFn:
    limit = int(limit/1024)
    return RAM_G(limit)
