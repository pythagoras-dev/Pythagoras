from persidict import FileDirDict

from pythagoras import InconsistentChangeOfImmutableItem
from pythagoras._800_persidict_extensions.first_entry_dict import FirstEntryDict

import pytest

def test_first_entry_dict_no_checks(tmpdir):
    d = FileDirDict(tmpdir, immutable_items=True)
    fed = FirstEntryDict(d, p_consistency_checks=None)
    for i in range(1,100):
        key = "a_"+str(i)
        value = i*i
        fed[key] = value
        assert fed[key] == value
        fed[key] = 2
        assert fed[key] == value
        fed[key] = value
        assert fed[key] == value
        assert len(fed) == i

def test_first_entry_dict_pchecks_zero(tmpdir):
    d = FileDirDict(tmpdir, immutable_items=True)
    fed = FirstEntryDict(d, p_consistency_checks=0)
    for i in range(1,100):
        key = "a_"+str(i)
        value = i*i
        fed[key] = value
        assert fed[key] == value
        fed[key] = 2
        assert fed[key] == value
        fed[key] = value
        assert fed[key] == value
        assert len(fed) == i

def test_first_entry_dict_pchecks_one(tmpdir):
    d = FileDirDict(tmpdir, immutable_items=True)
    fed = FirstEntryDict(d, p_consistency_checks=1)
    for i in range(1,100):
        key = "a_"+str(i)
        value = i*i*i
        fed[key] = value
        assert fed[key] == value
        with pytest.raises(InconsistentChangeOfImmutableItem):
            fed[key] = 3
        assert fed[key] == value
        fed[key] = value
        assert fed[key] == value
        with pytest.raises(InconsistentChangeOfImmutableItem):
            fed[key] = -i
        assert len(fed) == i

def test_firs_entry_dict_wrong_init_params(tmpdir):
    with pytest.raises(Exception):
        fed = FirstEntryDict({}, p_consistency_checks=None)

    with pytest.raises(Exception):
        fed = FirstEntryDict(
            FileDirDict(tmpdir, immutable_items=True)
            , p_consistency_checks=1.2)

    with pytest.raises(Exception):
        fed = FirstEntryDict(
            FileDirDict(tmpdir, immutable_items=True)
            , p_consistency_checks=-0.1)

    with pytest.raises(Exception):
        fed = FirstEntryDict(
            FileDirDict(tmpdir, immutable_items=False))