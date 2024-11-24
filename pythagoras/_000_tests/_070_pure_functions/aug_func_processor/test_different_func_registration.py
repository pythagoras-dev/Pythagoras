import pytest

from pythagoras import AutonomousCodePortal, _PortalTester
from pythagoras._070_pure_functions.process_augmented_func_src import (
    process_augmented_func_src)

src_1_good ="""
@pth.autonomous()
def f_1():
    pass
"""

src_2_bad ="""
@pth.autonomous() # this is a decorator
def f_1(): 
    print()
"""



def test_basic_func_registration(tmpdir):
    with _PortalTester(AutonomousCodePortal, tmpdir) as t:
        portal = t.portal

        assert len(portal.known_functions) == 1

        process_augmented_func_src(src_1_good)
        process_augmented_func_src(src_1_good)
        assert len(portal.known_functions) == 1
        assert len(portal.known_functions[portal.default_island_name]) == 1

        with pytest.raises(Exception):
            process_augmented_func_src(src_2_bad)