import inspect, autopep8

from pythagoras import _PortalTester
from pythagoras._020_ordinary_code_portals import get_normalized_function_source
from pythagoras._020_ordinary_code_portals import OrdinaryFn, OrdinaryCodePortal


def f_docstring():
    """ This is a CRAZY docstring"""
    def internal(a:int):
        """ This is another CRAZY docstring"""
        b=24
        return a+b
    class A:
        """ This is a third CRAZY docstring"""
        def __init__(self):
            pass
    return 123456

def f_comments():
    def internal(a:int):
        b=24
        # This is a STRANGE comment
        return a+b
    return internal(58)


def test_basics():
    no_docsting = get_normalized_function_source(f_docstring)
    assert "CRAZY" in inspect.getsource(f_docstring)
    assert "CRAZY" not in no_docsting
    assert no_docsting != autopep8.fix_code(inspect.getsource(f_docstring))
    assert no_docsting == autopep8.fix_code(no_docsting)

    no_comments = get_normalized_function_source(f_comments)
    assert "STRANGE" in inspect.getsource(f_comments)
    assert "STRANGE" not in no_comments
    assert no_comments != autopep8.fix_code(inspect.getsource(f_comments))
    assert no_comments == autopep8.fix_code(no_comments)


def a2(x): # a sample function to test
    print(10 # Why do I sit here?
        ,20)
    return x*x

def test_inclosed():
    global a2
    old_a2 = get_normalized_function_source(a2)
    del a2

    def a2(x):

        print (10, 20)
        # unneeded comment
        return (x * x)

    new_a2 = get_normalized_function_source(a2)
    assert old_a2 == new_a2
    assert new_a2 == autopep8.fix_code(new_a2)


def a3(x): # a sample function to test
    if x>0: return x*x*x
    elif x<100_000_000: return -x*x*x
    else: return 0

def test_inclosed2():
    global a3
    old_a3 = get_normalized_function_source(a3)
    del a3
    def a3(x):
        """ another version of the same function
        this is a docstring
        """
        if x > 0:
            return x * x * x
        elif x < 100000000:
            return -x * x * x
        else:
            return 0

    new_a3 = get_normalized_function_source(a3)
    assert old_a3 == new_a3
    assert new_a3 == autopep8.fix_code(new_a3)


def test_different(tmpdir):
    all_funcs = [f_docstring, f_comments, test_basics, test_inclosed
                , test_inclosed2, a2, a3, test_different]
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        for f1 in all_funcs:
            for f2 in all_funcs:
                if f1 is f2:
                    assert (get_normalized_function_source(f1)
                            == get_normalized_function_source(f2))
                    assert (get_normalized_function_source(
                                OrdinaryFn(f1, portal=t.portal))
                            == get_normalized_function_source(f2))
                else:
                    assert (get_normalized_function_source(f1)
                            != get_normalized_function_source(f2))
                    assert (get_normalized_function_source(
                                OrdinaryFn(f1, portal = t.portal))
                            != get_normalized_function_source(f2))


def a4(x:int)->float:
    if x>0:
        result:float =  x*x*x
        return result
    elif x<100_000_000: return -x*x*x
    else: return 0

def test_type_annotations():
    global a4
    old_a4 = get_normalized_function_source(a3)
    del a4
    def a4(x):
        if x > 0:
            result =  x * x * x
            return result
        elif x < 100000000:
            return -x * x * x
        else:
            return 0

    new_a4 = get_normalized_function_source(a3)
    assert old_a4 == new_a4
    assert new_a4 == autopep8.fix_code(new_a4)