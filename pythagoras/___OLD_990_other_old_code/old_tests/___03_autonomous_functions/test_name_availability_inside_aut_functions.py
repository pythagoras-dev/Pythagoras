import pytest
import pythagoras as pth

from pythagoras.___07_mission_control.global_state_management import (
    _force_initialize)

def test_name_availability(tmpdir):
    with _force_initialize(tmpdir, n_background_workers=0):

        @pth.autonomous()
        def my_good_function():
            result = bool(pth)
            result &= bool(pth.post_event)
            result &= bool(pth.autonomous)
            result &= bool(post_event)
            return result

        assert my_good_function()

        # with pytest.raises(NameError):
        @pth.autonomous()
        def my_bad_function():
            return bool(pytest)

        with pytest.raises(AssertionError):
            my_bad_function()

        @pth.autonomous()
        def my_2nd_bad_function():
            return bool(pythagoras)

        with pytest.raises(AssertionError):
            my_2nd_bad_function()