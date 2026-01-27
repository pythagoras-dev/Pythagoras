

from pythagoras import pure, _PortalTester, SwarmingPortal
from pythagoras._350_protected_code_portals.package_manager import *
from pythagoras.core import get


@pure()
def very_donothing_swarming_function(n:int):
    return 12345*n


def test_donothing_swarmig(tmpdir):
    """Test if package installer installs a package.
    """

    with _PortalTester(SwarmingPortal, tmpdir, exact_n_workers = 2):

        sync_res= very_donothing_swarming_function(n=1)
        assert sync_res == 12345

        async_res_addr = very_donothing_swarming_function.swarm(n=2)
        assert get(async_res_addr) == 2*12345
