from typing import TYPE_CHECKING

from pythagoras import autonomous, _PortalTester, AutonomousCodePortal

# The functions below use `self` which is injected into their global namespace
# at runtime by the portal framework when the decorated function is executed.
# This TYPE_CHECKING declaration makes `self` visible to static analysis tools
# (ruff, mypy, IDEs) without affecting runtime behavior.
if TYPE_CHECKING:
    from typing import Any
    self: Any = ...


def simple_a_function(a:int,b:int)->int:
    # assert isinstance(self,pth.AutonomousFn)
    print(f"{type(self)=}")
    return a+b

def another_a_function()->str:
    return self.name

def test_self_inside_autnms_fnc(tmpdir):
    global simple_a_function, another_a_function
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        simple_a_function = autonomous()(simple_a_function)
        assert simple_a_function(a=111,b=111000)==111111

        another_a_function = autonomous()(another_a_function)
        assert another_a_function()=="another_a_function"
