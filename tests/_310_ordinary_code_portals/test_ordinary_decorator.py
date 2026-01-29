import pytest
import pickle

import pythagoras as pth
from pythagoras import ordinary, OrdinaryCodePortal, _PortalTester, OrdinaryFn


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


def test_decorator_without_portal(tmpdir):
    """Test that decorator can be created without specifying a portal."""
    def test_func(x:int)->int:
        return x * 2
    
    # Decorator can be created without portal argument
    decorated = ordinary()(test_func)
    assert isinstance(decorated, OrdinaryFn)
    
    # Function executes correctly in a portal context
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        assert decorated(x=5) == 10
        assert decorated(x=7) == 14


def test_decorator_with_invalid_portal_type():
    """Test that TypeError is raised when portal is not OrdinaryCodePortal or None."""
    with pytest.raises(TypeError):
        ordinary(portal="invalid_portal")
    
    with pytest.raises(TypeError):
        ordinary(portal=123)


def test_decorator_not_picklable():
    """Test that decorator cannot be pickled."""
    decorator = ordinary()
    
    with pytest.raises(TypeError):
        pickle.dumps(decorator)



