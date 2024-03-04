from pythagoras._01_foundational_objects.value_addresses import ValueAddress
from pythagoras._06_mission_control.global_state_management import (
    initialize, _clean_global_state)
import pythagoras as pth


values_to_test = [1, 10, 10.0, "ten", "10", 10j
    , True, None, [1,2,3],(1,2,3), {1,2,3}, {1:2, None:4, "b": "c"}]

def test_value_address_basic(tmpdir):
    _clean_global_state()
    initialize(tmpdir)
    counter = 0
    for v in values_to_test:
        assert len(pth.global_value_store) == counter
        assert ValueAddress(v).get() == v
        assert ValueAddress(v).get() == v
        counter += 1
        assert len(pth.global_value_store) == counter

    _clean_global_state()
    initialize(tmpdir)
    assert len(pth.global_value_store) == counter

def test_nested_value_addrs(tmpdir):
    _clean_global_state()
    initialize(tmpdir)
    counter = 0
    for v in values_to_test:
        assert len(pth.global_value_store) == counter
        assert ValueAddress([ValueAddress(v)]).get()[0].get() == v
        assert ValueAddress([ValueAddress(v)]).get()[0].get() == v
        counter += 2
        assert len(pth.global_value_store) == counter

    _clean_global_state()
    initialize(tmpdir)
    assert len(pth.global_value_store) == counter
