"""Tests for KwArgs type invariants and packing/unpacking contracts.

Verifies that KwArgs, PackedKwArgs, and UnpackedKwArgs enforce proper
type boundaries and maintain documented invariants through pack/unpack cycles.
"""

import pytest

from pythagoras import KwArgs, PackedKwArgs, UnpackedKwArgs, ValueAddr
from pythagoras import LoggingCodePortal, _PortalTester


def test_base_kwargs_rejects_nested_base_kwargs(tmpdir):
    """Base KwArgs rejects other base KwArgs to prevent ambiguous nesting."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        parent = KwArgs()
        child = KwArgs(x=1, y=2)
        with pytest.raises(ValueError, match="Nested KwArgs are not allowed"):
            parent['child'] = child


@pytest.mark.parametrize("value_factory", [
    lambda: KwArgs(x=1, y=2).pack(),           # PackedKwArgs
    lambda: KwArgs(x=1, y=2).pack().unpack(),  # UnpackedKwArgs
    lambda: {'x': 1, 'y': 2},                   # dict
    lambda: ValueAddr(42),                      # ValueAddr
])
def test_base_kwargs_allows_non_base_kwargs_values(tmpdir, value_factory):
    """Base KwArgs allows PackedKwArgs, UnpackedKwArgs, dicts, and ValueAddr as values."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        parent = KwArgs()
        value = value_factory()
        parent['data'] = value
        assert parent['data'] == value


def test_packed_kwargs_only_accepts_value_addr(tmpdir):
    """PackedKwArgs enforces that all values are ValueAddr instances."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        packed = KwArgs(a=1).pack()

        # Should reject non-ValueAddr values
        for invalid_value in ['string', 42, {'x': 1}, KwArgs(x=1),
                              KwArgs(x=1).pack(), KwArgs(x=1).pack().unpack()]:
            with pytest.raises(ValueError, match="PackedKwArgs can only contain ValueAddr"):
                packed['new'] = invalid_value

        # Should accept ValueAddr
        addr = ValueAddr(42)
        packed['valid'] = addr
        assert packed['valid'] == addr


def test_packed_kwargs_from_pack_contains_only_value_addr(tmpdir):
    """PackedKwArgs created via pack() has only ValueAddr values."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        packed = KwArgs(a=1, b='hello', c=[1, 2, 3]).pack()
        assert all(isinstance(v, ValueAddr) for v in packed.values())


def test_unpacked_kwargs_rejects_value_addr_and_base_kwargs(tmpdir):
    """UnpackedKwArgs rejects ValueAddr and base KwArgs to ensure raw values only."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        unpacked = KwArgs(a=1).pack().unpack()

        with pytest.raises(ValueError, match="UnpackedKwArgs cannot contain ValueAddr"):
            unpacked['new'] = ValueAddr(42)

        with pytest.raises(ValueError, match="UnpackedKwArgs cannot contain.*base KwArgs"):
            unpacked['new'] = KwArgs(x=1)


@pytest.mark.parametrize("value_factory", [
    lambda: KwArgs(x=1, y=2).pack(),            # PackedKwArgs
    lambda: KwArgs(x=1, y=2).pack().unpack(),   # UnpackedKwArgs
    lambda: 'hello',                             # string
    lambda: 42,                                  # int
    lambda: [1, 2, 3],                          # list
    lambda: {'x': 1},                           # dict
])
def test_unpacked_kwargs_allows_regular_and_snapshot_values(tmpdir, value_factory):
    """UnpackedKwArgs allows raw values and KwArgs snapshots (Packed/Unpacked)."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        unpacked = KwArgs(a=1).pack().unpack()
        value = value_factory()
        unpacked['data'] = value
        assert unpacked['data'] == value


def test_unpacked_kwargs_from_unpack_contains_no_value_addr(tmpdir):
    """UnpackedKwArgs created via unpack() has no ValueAddr values."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        packed = KwArgs(a=1, b='hello', c=[1, 2, 3]).pack()
        unpacked = packed.unpack()
        assert not any(isinstance(v, ValueAddr) for v in unpacked.values())


def test_kwargs_snapshots_survive_pack_unpack_cycle(tmpdir):
    """PackedKwArgs and UnpackedKwArgs as values survive pack/unpack cycles."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        # PackedKwArgs as value
        inner_packed = KwArgs(x=1, y=2).pack()
        outer = KwArgs(data=inner_packed)
        retrieved = outer.pack().unpack()['data']
        assert isinstance(retrieved, PackedKwArgs)
        assert retrieved == inner_packed

        # UnpackedKwArgs as value
        inner_unpacked = KwArgs(a=3, b=4).pack().unpack()
        outer = KwArgs(data=inner_unpacked)
        retrieved = outer.pack().unpack()['data']
        assert isinstance(retrieved, UnpackedKwArgs)
        assert retrieved == inner_unpacked


def test_validator_scenario_with_packed_kwargs_as_argument(tmpdir):
    """Scenario from failing tests: validator receives packed_kwargs as data."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        # Function arguments are packed
        function_args = KwArgs(a=1, b=2).pack()
        fn_addr = ValueAddr('some_function')

        # Validator receives these as kwargs (PackedKwArgs is passed as value)
        validator_kwargs = KwArgs(packed_kwargs=function_args, fn_addr=fn_addr)

        # LoggingFn.execute() packs them again
        packed_validator_kwargs = validator_kwargs.pack()
        assert all(isinstance(v, ValueAddr) for v in packed_validator_kwargs.values())

        # Validator can unpack and access the original PackedKwArgs
        unpacked = packed_validator_kwargs.unpack()
        assert isinstance(unpacked['packed_kwargs'], PackedKwArgs)
        assert unpacked['fn_addr'] == 'some_function'


@pytest.mark.parametrize("n_packs", [2, 3, 5])
def test_multiple_pack_operations_are_safe(tmpdir, n_packs):
    """Multiple pack() calls create equivalent PackedKwArgs with same content."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        result = KwArgs(x=1, y=2)
        for _ in range(n_packs):
            result = result.pack()

        assert isinstance(result, PackedKwArgs)
        assert all(isinstance(v, ValueAddr) for v in result.values())
        assert result.unpack() == {'x': 1, 'y': 2}


@pytest.mark.parametrize("n_unpacks", [2, 3, 5])
def test_multiple_unpack_operations_are_safe(tmpdir, n_unpacks):
    """Multiple unpack() calls create equivalent UnpackedKwArgs with same content."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        result = KwArgs(a=10, b=20).pack()
        for _ in range(n_unpacks):
            result = result.unpack()

        assert isinstance(result, UnpackedKwArgs)
        assert not any(isinstance(v, ValueAddr) for v in result.values())
        assert dict(result) == {'a': 10, 'b': 20}


def test_pack_unpack_cycles_preserve_values(tmpdir):
    """Alternating pack/unpack cycles preserve original values."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        original = KwArgs(data=42)

        # Multiple pack/unpack cycles
        result = original.pack().unpack().pack().unpack().pack().unpack()

        assert isinstance(result, UnpackedKwArgs)
        assert result['data'] == 42


def test_pack_is_content_idempotent(tmpdir):
    """pack().pack() produces equivalent content to pack()."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        original = KwArgs(x=1, y=2, z=3)

        single_pack = original.pack()
        double_pack = original.pack().pack()

        assert dict(single_pack) == dict(double_pack)
        assert dict(single_pack.unpack()) == dict(double_pack.unpack())


def test_unpack_is_content_idempotent(tmpdir):
    """unpack().unpack() produces equivalent content to unpack()."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        packed = KwArgs(a=10, b=20, c=30).pack()

        single_unpack = packed.unpack()
        double_unpack = packed.unpack().unpack()

        assert dict(single_unpack) == dict(double_unpack)
        assert dict(single_unpack.pack()) == dict(double_unpack.pack())


def test_packed_kwargs_pickle_stable_regardless_of_insertion_order(tmpdir):
    """PackedKwArgs with same content but different insertion order produce identical pickles."""
    import pickle

    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        # Create PackedKwArgs with same content but different insertion orders
        pk1 = KwArgs(x=1).pack()
        pk1['a'] = ValueAddr(1)
        pk1['b'] = ValueAddr(2)
        pk1['c'] = ValueAddr(3)

        pk2 = KwArgs(x=1).pack()
        pk2['c'] = ValueAddr(3)
        pk2['b'] = ValueAddr(2)
        pk2['a'] = ValueAddr(1)

        # Keys should be in different order before pickling
        assert list(pk1.keys()) != list(pk2.keys())

        # Pickles should be identical (sorting happens in __reduce__)
        pickled1 = pickle.dumps(pk1)
        pickled2 = pickle.dumps(pk2)
        assert pickled1 == pickled2

        # After unpickling, keys should be sorted
        unpk1 = pickle.loads(pickled1)
        unpk2 = pickle.loads(pickled2)
        assert list(unpk1.keys()) == list(unpk2.keys()) == sorted(pk1.keys())


def test_unpacked_kwargs_pickle_stable_regardless_of_insertion_order(tmpdir):
    """UnpackedKwArgs with same content but different insertion order produce identical pickles."""
    import pickle

    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        # Create UnpackedKwArgs with same content but different insertion orders
        uk1 = KwArgs(x=1).pack().unpack()
        uk1['a'] = 1
        uk1['b'] = 2
        uk1['c'] = 3

        uk2 = KwArgs(x=1).pack().unpack()
        uk2['c'] = 3
        uk2['b'] = 2
        uk2['a'] = 1

        # Keys should be in different order before pickling
        assert list(uk1.keys()) != list(uk2.keys())

        # Pickles should be identical
        pickled1 = pickle.dumps(uk1)
        pickled2 = pickle.dumps(uk2)
        assert pickled1 == pickled2

        # After unpickling, keys should be sorted
        unpk1 = pickle.loads(pickled1)
        unpk2 = pickle.loads(pickled2)
        assert list(unpk1.keys()) == list(unpk2.keys()) == sorted(uk1.keys())


def test_base_kwargs_pickle_stable_regardless_of_insertion_order(tmpdir):
    """Base KwArgs with same content but different insertion order produce identical pickles."""
    import pickle

    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        # Create KwArgs with same content but different insertion orders
        k1 = KwArgs(x=1)
        k1['a'] = 1
        k1['b'] = 2
        k1['c'] = 3

        k2 = KwArgs(x=1)
        k2['c'] = 3
        k2['b'] = 2
        k2['a'] = 1

        # Keys should be in different order before pickling
        assert list(k1.keys()) != list(k2.keys())

        # Pickles should be identical
        pickled1 = pickle.dumps(k1)
        pickled2 = pickle.dumps(k2)
        assert pickled1 == pickled2

        # After unpickling, keys should be sorted
        unpk1 = pickle.loads(pickled1)
        unpk2 = pickle.loads(pickled2)
        assert list(unpk1.keys()) == list(unpk2.keys()) == sorted(k1.keys())


@pytest.mark.parametrize("kwargs_type,factory", [
    (KwArgs, lambda: KwArgs(x=1)),
    (PackedKwArgs, lambda: KwArgs(x=1).pack()),
    (UnpackedKwArgs, lambda: KwArgs(x=1).pack().unpack()),
])
def test_kwargs_equality_independent_of_insertion_order(tmpdir, kwargs_type, factory):
    """KwArgs instances with same content are equal regardless of insertion order."""
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        obj1 = factory()
        obj2 = factory()

        # Add same items in different orders
        if kwargs_type == PackedKwArgs:
            obj1['a'] = ValueAddr(1)
            obj1['b'] = ValueAddr(2)
            obj2['b'] = ValueAddr(2)
            obj2['a'] = ValueAddr(1)
        else:
            obj1['a'] = 1
            obj1['b'] = 2
            obj2['b'] = 2
            obj2['a'] = 1

        # Keys in different order
        assert list(obj1.keys()) != list(obj2.keys())

        # But objects should be equal
        assert obj1 == obj2
        assert dict(obj1) == dict(obj2)
