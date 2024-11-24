from pythagoras.___07_mission_control.global_state_management import (
    _force_initialize)
from pythagoras._01_99_foundational_objects.value_addresses import ValueAddr
from pythagoras.___03_OLD_autonomous_functions import *

import pythagoras as pth

def f(a, b):
    return a + b

def test_load_save(tmpdir):

    with _force_initialize(
            base_dir=tmpdir
            , default_island_name="test"
            , n_background_workers=0):

        f_1 = AutonomousFn(f, island_name="test",strictly_autonomous=True)
        f_address = ValueAddr(f_1)

        f_2 = f_address.get()
        assert f_2(a=1, b=2) == f(a=1, b=2) == 3
        assert f_2.fn_name == f_1.fn_name
        assert f_2.fn_source_code == f_1.fn_source_code
        assert f_2.island_name == f_1.island_name

        f_island_name = f_1.island_name
        f_naked_source_code = f_1.fn_source_code
        f_name = f_1.fn_name

        f_address._invalidate_cache()


    with _force_initialize(
            base_dir=tmpdir
            , default_island_name="test"
            , n_background_workers=0):


        del f_address._portal

        f_address._portal = pth.default_portal

        f_3 = f_address.get()
        assert f_3(a=1, b=2) == f(a=1, b=2) == 3
        assert f_3.fn_name == f_name
        assert f_3.fn_source_code == f_naked_source_code
        assert f_3.island_name == f_island_name
