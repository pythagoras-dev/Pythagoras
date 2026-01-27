from typing import TYPE_CHECKING

import pythagoras as pth
from pythagoras import ordinary

# The functions below use `self` which is injected into their global namespace
# at runtime by the portal framework when the decorated function is executed.
# This TYPE_CHECKING declaration makes `self` visible to static analysis tools
# (ruff, mypy, IDEs) without affecting runtime behavior.
if TYPE_CHECKING:
    from typing import Any
    self: Any = ...


def simple_o_function(a:int,b:int)->int:
    assert isinstance(self,pth.OrdinaryFn)
    return a+b

def test_simple(tmpdir):
    global simple_o_function
    with pth._PortalTester(pth.OrdinaryCodePortal, root_dict=tmpdir):
        simple_o_function = ordinary()(simple_o_function)
        assert simple_o_function(a=11,b=1100)==1111
