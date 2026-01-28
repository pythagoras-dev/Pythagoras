from copy import copy
from typing import Any

import pytest

from pythagoras._210_basic_portals import (
    get_current_portal, _PortalTester)
from pythagoras._220_data_portals import *



values_to_test = [1, 10, 10.0, "ten", "10", 10j
    , True, None, [1,2,3],(1,2,3), {1,2,3}, {"zxcvbn":2, "qwerty":4, "b": "c"}]


def test_value_address_basic(tmpdir):
    # tmpdir = 3*"VALUE_ADDRESS_BASIC_" + str(int(time.time())) + "_" + str(p)
    counter = 0

    with _PortalTester(DataPortal,tmpdir):
        for v in values_to_test:
            assert len(get_current_portal().global_value_store) == counter
            assert ValueAddr(v).get() == v
            assert ValueAddr(v).get() == v
            counter += 1
            assert len(get_current_portal().global_value_store) == counter

    with _PortalTester(DataPortal,tmpdir):
        assert len(get_current_portal().global_value_store) == counter


def test_value_address_with_typechecks(tmpdir):
    # tmpdir = 2*"VALUE_ADDRESS_WITH_TYPECHECKS_" + str(int(time.time())) + "_" + str(p)

    with _PortalTester(DataPortal,tmpdir):
        for v in values_to_test:
            assert ValueAddr(v).get(expected_type=type(v)) == v
            assert ValueAddr(v).get(expected_type=Any) == v
            assert ValueAddr(v).get(expected_type=object) == v
            assert ValueAddr(v).get() == v

            if not isinstance(v,str):
                with pytest.raises(TypeError):
                    ValueAddr(v).get(expected_type=str)

            if not isinstance(v,int):
                with pytest.raises(TypeError):
                    ValueAddr(v).get(expected_type=int)

            if not isinstance(v,list):
                with pytest.raises(TypeError):
                    ValueAddr(v).get(expected_type=list)



def test_nested_value_addrs(tmpdir):
    counter = 0

    with _PortalTester(DataPortal,tmpdir):
        for v in values_to_test:
            assert len(get_current_portal().global_value_store) == counter
            assert ValueAddr([ValueAddr(v)]).get()[0].get() == v
            assert ValueAddr([ValueAddr(v)]).get()[0].get() == v
            counter += 2
            assert len(get_current_portal().global_value_store) == counter

    with _PortalTester(DataPortal,tmpdir):
        assert len(get_current_portal().global_value_store) == counter


def test_value_address_constructor_with_two_portals(tmpdir):

    with _PortalTester(DataPortal,tmpdir):
        portal1 =DataPortal(tmpdir + "/t1")
        portal2 =DataPortal(tmpdir + "/t2")

        with portal1:
            addr1_10 = ValueAddr(10)
            with portal2:
                _addr2_10 = ValueAddr(10)
                _addr2_20 = ValueAddr(20)
                addr2_hihi = ValueAddr("hihi")


            assert len(portal1.global_value_store) == 1
            assert len(portal2.global_value_store) == 3

            assert addr1_10.get() == 10
            assert len(portal1.global_value_store) == 1
            assert len(portal2.global_value_store) == 3

            assert addr2_hihi.get() == "hihi"
            assert len(portal1.global_value_store) == 2
            assert len(portal2.global_value_store) == 3

            # with portal2:
            #     assert addr1_10.get() == 10
            #     assert len(portal1.global_value_store) == 2
            #     assert len(portal2.global_value_store) == 4



def test_value_address_ready_with_two_portals(tmpdir):

    with _PortalTester(DataPortal,tmpdir):
        portal1 =DataPortal(tmpdir + "/t1")
        portal2 =DataPortal(tmpdir + "/t2")

        with portal1:
            addr1_10 = ValueAddr(10)
            with portal2:
                _addr2_10 = ValueAddr(10)
                _addr2_20 = ValueAddr(20)
                addr2_hihi = ValueAddr("hihi")

            assert len(portal1.global_value_store) == 1
            assert len(portal2.global_value_store) == 3

            copy(addr1_10)
            assert len(portal1.global_value_store) == 1
            assert len(portal2.global_value_store) == 3

            addr1_hihi = copy(addr2_hihi)
            addr1_hihi._portal = portal1
            assert len(portal1.global_value_store) == 1
            assert len(portal2.global_value_store) == 3

            assert addr1_hihi.ready
            assert len(portal1.global_value_store) == 2
            assert len(portal2.global_value_store) == 3


def test_value_address_get_with_two_portals(tmpdir):

    with _PortalTester():
        portal1 =DataPortal(tmpdir + "/t1")
        portal2 =DataPortal(tmpdir + "/t2")

        with portal1:
            addr1_10 = ValueAddr(10)
            with portal2:
                _addr2_10 = ValueAddr(10)
                _addr2_20 = ValueAddr(20)
                addr2_hihi = ValueAddr("hihi")

            assert addr2_hihi.get() == "hihi"
            assert len(portal1.global_value_store) == 2
            assert len(portal2.global_value_store) == 3

            copy(addr1_10)
            assert len(portal1.global_value_store) == 2
            assert len(portal2.global_value_store) == 3

            addr1_hihi = copy(addr2_hihi)
            assert len(portal1.global_value_store) == 2
            assert len(portal2.global_value_store) == 3

            assert addr1_hihi.get() == "hihi"
            assert len(portal1.global_value_store) == 2
            assert len(portal2.global_value_store) == 3


def test_value_addr_rejects_uninitialized_object(tmpdir):
    """Test ValueError when creating ValueAddr from uninitialized object."""
    class MockUninitializedObj:
        def __init__(self):
            self._init_finished = False

    with _PortalTester(DataPortal, tmpdir):
        obj = MockUninitializedObj()
        with pytest.raises(ValueError, match="Cannot create ValueAddr for an uninitialized object"):
            ValueAddr(obj)


def test_value_addr_rejects_hashaddr_direct_conversion(tmpdir):
    """Test TypeError when creating ValueAddr directly from HashAddr."""
    class MockHashAddr(HashAddr):
        @property
        def ready(self):
            return True
        def get(self, timeout=None, expected_type=None):
            return 42

    with _PortalTester(DataPortal, tmpdir):
        hash_addr = MockHashAddr("descriptor", "1234567890")
        with pytest.raises(TypeError, match="get_ValueAddr is the only way to convert HashAddr into ValueAddr"):
            ValueAddr(hash_addr)


def test_value_addr_from_strings_without_readiness_check(tmpdir):
    """Test ValueAddr.from_strings() with assert_readiness=False."""
    with _PortalTester(DataPortal, tmpdir):
        ValueAddr(42)  # Store a value first
        addr = ValueAddr.from_strings(
            descriptor="int",
            hash_signature=ValueAddr(42).hash_signature,
            assert_readiness=False
        )
        assert addr.descriptor == "int"
        assert len(addr.hash_signature) >= 10


def test_value_addr_from_strings_with_readiness_check(tmpdir):
    """Test ValueAddr.from_strings() with assert_readiness=True."""
    with _PortalTester(DataPortal, tmpdir):
        original = ValueAddr(42)
        addr = ValueAddr.from_strings(
            descriptor=original.descriptor,
            hash_signature=original.hash_signature,
            assert_readiness=True
        )
        assert addr.get() == 42


def test_value_addr_from_strings_fails_when_not_ready(tmpdir):
    """Test from_strings() raises ValueError when value not ready."""
    with _PortalTester(DataPortal, tmpdir):
        with pytest.raises(ValueError, match="Address is not ready for retrieving data"):
            ValueAddr.from_strings(
                descriptor="nonexistent",
                hash_signature="1234567890abc",
                assert_readiness=True
            )


def test_value_addr_pickle_unpickle_roundtrip(tmpdir):
    """Test ValueAddr can be pickled and unpickled correctly."""
    import pickle

    with _PortalTester(DataPortal, tmpdir):
        original_addr = ValueAddr(42)
        pickled = pickle.dumps(original_addr)
        unpickled_addr = pickle.loads(pickled)

        assert unpickled_addr.descriptor == original_addr.descriptor
        assert unpickled_addr.hash_signature == original_addr.hash_signature
        assert unpickled_addr.get() == 42