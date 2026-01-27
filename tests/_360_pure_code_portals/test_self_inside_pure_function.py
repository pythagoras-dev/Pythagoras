from typing import TYPE_CHECKING

from pythagoras import autonomous, _PortalTester, AutonomousCodePortal

# The functions below use `self` which is injected into their global namespace
# at runtime by the portal framework when the decorated function is executed.
# This TYPE_CHECKING declaration makes `self` visible to static analysis tools
# (ruff, mypy, IDEs) without affecting runtime behavior.
if TYPE_CHECKING:
    from typing import Any
    self: Any = ...


def simple_p_function(a:int,b:int)->int:
    # assert isinstance(self,pth.AutonomousFn)
    print(f"{type(self)=}")
    return a+b

def another_p_function()->str:
    return self.name

def test_simple(tmpdir):
    global simple_p_function, another_p_function
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        simple_a_function = autonomous()(simple_p_function)
        assert simple_a_function(a=111,b=111000)==111111

        another_p_function = autonomous()(another_p_function)
        assert another_p_function()=="another_p_function"
