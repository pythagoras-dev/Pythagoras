import pytest

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure



def bad_f(*args):
    return args[0]

def good_f(a):
    return a

def test_positional_args(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        global bad_f, good_f

        with pytest.raises(Exception):
            bad_f = pure()(bad_f)

        good_f = pure()(good_f)

        assert good_f(a=10) == 10
        with pytest.raises(Exception):
            good_f(10)
