import pythagoras as pth
from pythagoras import ordinary


def simple_o_function(a:int,b:int)->int:
    assert isinstance(self,pth.OrdinaryFn)
    return a+b

def test_simple(tmpdir):
    global simple_o_function
    with pth._PortalTester(pth.OrdinaryCodePortal, root_dict=tmpdir) as t:
        simple_o_function = ordinary()(simple_o_function)
        assert simple_o_function(a=11,b=1100)==1111