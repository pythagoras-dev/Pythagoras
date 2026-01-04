import pytest
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._340_autonomous_code_portals import *


def test_non_ordinary_callables_autonomous_decorator(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        with pytest.raises(Exception):
            autonomous()(lambda x: x**2)

        class A:
            def __call__(self, x):
                return x**2

            def a_method(self,x):
                return x**2

            @classmethod
            def c_method(cls,x):
                return x**2

        a = A()

        with pytest.raises(Exception):
            autonomous()(A)

        with pytest.raises(Exception):
            autonomous()(a.a_method)

        with pytest.raises(Exception):
            autonomous()(A.c_method)

        async def fff_fff_fff():
            return

        with pytest.raises(Exception):
            autonomous()(fff_fff_fff)