from pythagoras.___07_mission_control.global_state_management import (
    _force_initialize)
from pythagoras._01_99_foundational_objects.value_addresses import ValueAddr
from pythagoras.___03_OLD_autonomous_functions import *

import pytest

import pythagoras as pth


def test_load_save_error(tmpdir):
    with _force_initialize(base_dir=tmpdir
               , default_island_name="123"
               , n_background_workers=0):
        assert len(pth.default_portal.value_store) == 0
        def f(a, b):
            return a + b

        f_1 = AutonomousFn(f, island_name="123")
        f_1_address = ValueAddr(f_1)
        assert len(pth.default_portal.value_store) == 1
        f_1_address._invalidate_cache()

    with _force_initialize(base_dir=tmpdir
            , default_island_name="123"
            , n_background_workers=0):

        def f(a, b):
            return a * b * 2

        f_2 = AutonomousFn(f, island_name="123")
        f_2_address = ValueAddr(f_2)
        assert len(pth.default_portal.value_store) == 2
        f_2_address._invalidate_cache()

    with _force_initialize(base_dir=tmpdir
            , default_island_name="123"
            , n_background_workers=0):

        f_1_address._portal = pth.default_portal
        f_2_address._portal = pth.default_portal

        f_a = f_1_address.get()
        assert f_a(a=1, b=2) == 3

        with pytest.raises(Exception):
            f_b = f_2_address.get()