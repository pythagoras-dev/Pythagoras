import pytest

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._070_pure_functions.pure_core_classes import (
    PureCodePortal,PureFnExecutionResultAddr)
from pythagoras._070_pure_functions.pure_decorator import pure
from pythagoras._070_pure_functions.purity_checks import is_pure


def bad_f(*args):
    return args[0]

def good_f(a):
    return a

def test_positional_args(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        global bad_f, good_f

        with pytest.raises(Exception):
            bad_f = pure()(bad_f)

        good_f = pure()(good_f)

        assert good_f(a=10) == 10
        with pytest.raises(Exception):
            good_f(10)
