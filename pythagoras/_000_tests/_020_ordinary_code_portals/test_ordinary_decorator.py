import pythagoras as pth
from pythagoras import ordinary, OrdinaryCodePortal, _PortalTester


def simple_function_1(a:int,b:int)->int:
    return a+b

def simple_function_2(a:int,b:int)->int:
    return a*b

def test_simple(tmpdir):
    global simple_function_1, simple_function_2
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        simple_function_1 = pth.ordinary(t.portal)(simple_function_1)
        simple_function_2 = ordinary(t.portal)(simple_function_2)
        assert simple_function_1(a=1,b=2)==3
        assert simple_function_2(a=2,b=3)==6



