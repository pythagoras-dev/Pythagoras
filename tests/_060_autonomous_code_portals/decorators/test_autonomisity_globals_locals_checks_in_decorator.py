import pytest
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._060_autonomous_code_portals import *

import sys


def test_globals_in_autonomous(tmpdir):
    """Test autonomous function wrapper with global objects."""

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        @autonomous()
        def good_global_f():
            import math
            return math.sqrt(4)

        assert isinstance(good_global_f, AutonomousFn)

        from math import sqrt

        def bad_global_f1():
            return sqrt(4)

        def bad_global_f2():
            return sys.version

        assert good_global_f() == 2

        with pytest.raises(Exception):
            bad_global_f1 = autonomous()(bad_global_f1)

        with pytest.raises(Exception):
            bad_global_f1 = autonomous()(bad_global_f1)



def test_locals_in_autonomous(tmpdir):
    """Test autonomous function wrapper with local objects."""
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        import random

        def bad_local_f3():
            x = 3
            return random.random()

        with pytest.raises(Exception):
            bad_local_f3 = autonomous()(bad_local_f3)

        @autonomous()
        def good_local_f2():
            import random
            x=3
            return random.random() + 1

        assert good_local_f2()


demo_global_var=20

def test_nonlocals_in_autonomous(tmpdir):
    """Test autonomous function wrapper with local objects."""
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        demo_nonlocal_var=10

        def bad_nonlocal_f():
            nonlocal demo_nonlocal_var
            return demo_nonlocal_var*2

        assert bad_nonlocal_f()==20

        with pytest.raises(Exception):
            bad_nonlocal_f = autonomous()(bad_nonlocal_f)

def test_globals_2_in_autonomous(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        with pytest.raises(Exception):
            @autonomous()
            def bad_global_f():
                global demo_global_var
                return demo_global_var * 2

        def bad_global_ffff():
            global demo_global_var
            return demo_global_var * 10

        assert bad_global_ffff()==200

        with pytest.raises(Exception):
            bad_global_ffff = autonomous()(bad_global_ffff)


