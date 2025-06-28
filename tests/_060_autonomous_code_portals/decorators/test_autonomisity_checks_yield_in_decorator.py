import pytest
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._060_autonomous_code_portals import *


def test_yield(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        with pytest.raises(Exception):
            @autonomous()
            def f():
                yield 1

def test_nested_yield(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        @autonomous()
        def f_y():
            def g():
                yield 1
            return list(g())
        assert f_y() == [1]