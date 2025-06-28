from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._800_signatures_and_converters.current_date_gmt_str import (
    current_date_gmt_string)
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure
import pytest


def test_zero_div(tmpdir):
    # tmpdir=5*"ZERO_DIV_"+str(int(time.time()))
    with _PortalTester(PureCodePortal, tmpdir) as t:
        assert len(t.portal._crash_history) == 0
        date_str_1 = current_date_gmt_string()

        @pure()
        def zero_div(x:float)->float:
            return x/0

        with pytest.raises(ZeroDivisionError):
            zero_div(x=2024)

        date_str_2 = current_date_gmt_string()

        assert len(t.portal._crash_history) >= 1
        for event_id  in list(t.portal._crash_history):
            assert event_id[0] in [date_str_1, date_str_2]

def test_sqrt(tmpdir):
    # tmpdir = 8 * "SQRT_" + str(int(time.time()))
    with _PortalTester(PureCodePortal, tmpdir) as t:

        date_str_1 = current_date_gmt_string()

        @pure()
        def my_sqrt(x: float) -> float:
            from math import sqrt
            return sqrt(x)

        n = 5
        for i in range(n):
            if i <= 0:
                my_sqrt(x=-i)
                continue
            with pytest.raises(ValueError):
                my_sqrt(x=-i)

        date_str_2 = current_date_gmt_string()

        assert len(t.portal._crash_history) == n-1
        for event_id in list(t.portal._crash_history):
            assert event_id[0] in [date_str_1, date_str_2]