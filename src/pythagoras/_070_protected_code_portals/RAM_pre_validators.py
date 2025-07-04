from .._070_protected_code_portals import SimplePreValidatorFn
from .._060_autonomous_code_portals import autonomous
from .OK_const import OK, OKClass
from .system_utils import *


# def free_ram_bytes(packed_kwargs, fn_addr, required_memory):
#     import psutil
#     mem_info = psutil.virtual_memory()
#     if mem_info.available >= required_memory:
#         return OK
#
#
# def RAM_K(limit:int) -> AutonomousFn:
#     global free_ram_bytes
#     if not isinstance(free_ram_bytes, AutonomousFn):
#         free_ram_bytes = autonomous()(free_ram_bytes)
#     limit = int(limit/1024)
#     assert limit > 0
#     return free_ram_bytes.fix_kwargs(required_memory = limit)
#
#
# def RAM_M(limit:int) -> AutonomousFn:
#     limit = int(limit/1024)
#     return RAM_K(limit)
#
#
# def RAM_G(limit:int) -> AutonomousFn:
#     limit = int(limit/1024)
#     return RAM_M(limit)
#
#
# def RAM_T(limit:int) -> AutonomousFn:
#     limit = int(limit/1024)
#     return RAM_G(limit)

@autonomous()
def at_least_X_G_RAM_free_check(x:int)->bool|OKClass:
    ram = pth.get_unused_ram_mb() / 1024
    if ram >= x:
        return pth.OK
    else:
        return False

def unused_ram(Gb:int):
    assert isinstance(Gb, int)
    assert Gb > 0
    return SimplePreValidatorFn(at_least_X_G_RAM_free_check.fix_kwargs(x=Gb))

at_least_1_G_RAM_free = unused_ram(Gb=1)
at_least_2_G_RAM_free = unused_ram(Gb=2)
at_least_4_G_RAM_free = unused_ram(Gb=4)
at_least_8_G_RAM_free = unused_ram(Gb=8)
at_least_16_G_RAM_free = unused_ram(Gb=16)
at_least_32_G_RAM_free = unused_ram(Gb=32)
at_least_64_G_RAM_free = unused_ram(Gb=64)
at_least_128_G_RAM_free = unused_ram(Gb=128)
at_least_256_G_RAM_free = unused_ram(Gb=256)
at_least_512_G_RAM_free = unused_ram(Gb=512)