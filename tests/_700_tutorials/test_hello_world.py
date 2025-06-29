import time

from pythagoras.core import *
import pythagoras as pth
#
# from pythagoras import PureFnExecutionResultAddr,SwarmingPortal, pure
#
#
# def get(l:list|set) -> list:
#     result = []
#     for i in l:
#         result.append(i.get())
# #     return result
#
# def ready(l) -> list:
#     result = True
#     for i in l:
#         assert isinstance(i, PureFnExecutionResultAddr)
#         result &= i.ready
#     return result

@pure()
def long_running(a:float, b:float, c:float) -> float:
    import time
    time.sleep(0)
    return a + 10*b + 100*c


def test_hello_world(tmpdir):
    portal = SwarmingPortal(tmpdir, max_n_workers=5)
    global long_running

    l = []
    for i in range(2):
        for ii in range(2):
            for iii in range(2):
                    l.append(long_running.swarm(a=i, b=ii, c=iii))
    num_seconds = 0
    time_to_wait = 1
    while not ready(l):
        time.sleep(time_to_wait)
        num_seconds += time_to_wait
        print(f"waiting... {num_seconds} seconds")

    print(sorted(get(l)))






