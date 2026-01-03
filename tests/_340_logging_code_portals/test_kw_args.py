import pytest

from pythagoras import ValueAddr, DataPortal, PackedKwArgs, get_random_signature, UnpackedKwArgs
from pythagoras import _PortalTester
from pythagoras import KwArgs


dict1 = {"yyy":-100, "a": 1, "b": 2, "c": 3}
dict2 = { "e": 0, "c":1, "b":2, "a":3}
dict3 = {get_random_signature():get_random_signature() for i in range(100)}
dict4 = {get_random_signature():get_random_signature() for j in range(150)}

dicts_to_test = [dict1, dict2, dict3, dict4]

@pytest.mark.parametrize("p",[0,0.5,1])
def test_sortedkwargs(tmpdir,p):
    """Test PackedKwArgs constructor and basic functionality."""

    with _PortalTester(DataPortal, root_dict=tmpdir
            ,p_consistency_checks=p) as t:

        for i in range(4):
            for sample_dict in dicts_to_test:
                assert list(sample_dict.keys()) != sorted(sample_dict.keys())

                n_pka = KwArgs(**sample_dict)
                pka = KwArgs(**sample_dict).pack()
                n_pka = ValueAddr(n_pka).get()
                pka = ValueAddr(pka).get()

                assert list(pka.keys()) == sorted(pka.keys()) == list(n_pka.keys())

                for k in pka:
                    assert pka[k] == ValueAddr(sample_dict[k])

                assert KwArgs(**pka).unpack() == sample_dict == n_pka


def test_sortedkwargs_2portals(tmpdir):
    with _PortalTester(DataPortal, root_dict=tmpdir.mkdir("t1")) as t:
        p1 = t.portal
        p2 = DataPortal(root_dict=tmpdir.mkdir("t2"))
        sampe_dict = dict2
        pka = KwArgs(**sampe_dict).pack()
        assert len(p1._value_store) == 4
        assert len(p2._value_store) == 0

        with p2:
            pka = KwArgs(**sampe_dict).pack()
        assert len(p1._value_store) == 4
        assert len(p2._value_store) == 4

        pka = KwArgs(**pka).pack()
        pka = KwArgs(**pka).pack()

        assert len(p1._value_store) == 4
        assert len(p2._value_store) == 4

@pytest.mark.parametrize("p",[0,0.5,1])
def test_sortedkwargs_save_load(tmpdir,p):
    """Test PackedKwArgs constructor and basic functionality."""
    for i in range(4):
        with _PortalTester(DataPortal, root_dict=tmpdir
                ,p_consistency_checks=p) as t:
            portal = t.portal
            sampe_dict = { "e": 0, "c":1, "b":2, "a":3}
            pka = KwArgs(**sampe_dict).pack()
            portal._value_store["PKA"] = pka
            new_pka = portal._value_store["PKA"]
            assert new_pka == pka
            assert type(new_pka) == type(pka) == PackedKwArgs

def test_hierarchy():
    assert issubclass(KwArgs, dict)
    assert issubclass(PackedKwArgs, dict)
    assert issubclass(UnpackedKwArgs, dict)

