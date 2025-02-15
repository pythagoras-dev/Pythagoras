from pythagoras import OrdinaryFn, _PortalTester, OrdinaryCodePortal


def simple_function(a:int,b:int) -> int:
    return a+b

def test_ordinary_function(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function)
        f = OrdinaryFn(f)

        result = f(a=1,b=2)
        assert result == 3

        result = f(a=2,b=3)
        assert result == 5

        result = f(a=3,b=4)
        assert result == 7



def fibonacci(n:int) -> int:
    if n < 2:
        return n
    return fibonacci(n=n-1) + fibonacci(n=n-2)

def test_ordinary_function_with_recursion(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(fibonacci)
        f = OrdinaryFn(f)

        result = f(n=10)
        assert result == 55

        result = f(n=6)
        assert result == 8

        result = f(n=7)
        assert result == 13

        result = f(n=9)
        assert result == 34

        result = f(n=8)
        assert result == 21




