from persidict import FileDirDict
from src.pythagoras._800_persidict_extensions.overlapping_multi_dict import OverlappingMultiDict


def test_single_filedirdict_pkl(tmpdir):
    d = OverlappingMultiDict(
        FileDirDict
        ,shared_subdicts_params=dict(base_dir=tmpdir)
        , pkl={})
    assert len(d.pkl) == 0
    d.pkl["hi"] = "hello"
    d.pkl["bye"] = "goodbye"
    assert d.pkl["hi"] == "hello"
    assert d.pkl["bye"] == "goodbye"
    assert len(d.pkl) == 2

def test_single_filedirdict_json(tmpdir):
    d = OverlappingMultiDict(
        FileDirDict
        , shared_subdicts_params=dict(base_dir=tmpdir)
        , json={})
    assert len(d.json) == 0
    d.json["hi"] = "hello"
    d.json["bye"] = "goodbye"
    assert d.json["hi"] == "hello"
    assert d.json["bye"] == "goodbye"
    assert len(d.json) == 2

def test_single_filedirdict_txt(tmpdir):
    d = OverlappingMultiDict(
        FileDirDict
        , shared_subdicts_params=dict(base_dir=tmpdir)
        , txt={"base_class_for_values": str})
    assert len(d.txt) == 0
    d.txt["hi"] = "hello"
    d.txt["bye"] = "goodbye"
    assert d.txt["hi"] == "hello"
    assert d.txt["bye"] == "goodbye"
    assert len(d.txt) == 2

def test_single_filedirdict_py(tmpdir):
    d = OverlappingMultiDict(
        FileDirDict
        , shared_subdicts_params=dict(base_dir=tmpdir)
        , py={"base_class_for_values": str})
    assert len(d.py) == 0
    d.py["hi"] = "hello"
    d.py["bye"] = "goodbye"
    assert d.py["hi"] == "hello"
    assert d.py["bye"] == "goodbye"
    assert len(d.py) == 2

def test_2_filedirdicts_py_txt(tmpdir):
    d = OverlappingMultiDict(
        FileDirDict
        ,shared_subdicts_params=dict(base_dir=tmpdir)
        , py={"base_class_for_values": str}
        , txt={"base_class_for_values": str})

    d.txt["hi"] = "hello"
    d.txt["bye"] = "goodbye"
    d.py["hi"] = "hello"
    d.py["hihi"] = "hellohello"
    d.py["hihihi"] = "hellohellohellow"
    assert d.txt["hi"] == "hello"
    assert d.txt["bye"] == "goodbye"
    assert d.py["hi"] == "hello"
    assert d.py["hihi"] == "hellohello"
    assert d.py["hihihi"] == "hellohellohellow"
    assert len(d.txt) == 2
    assert len(d.py) == 3

def test_4_persidicts_py_txt_json_pkl(tmpdir):
    d = OverlappingMultiDict(
        FileDirDict
        ,shared_subdicts_params=dict(base_dir=tmpdir)
        , py={"base_class_for_values": str}
        , txt={"base_class_for_values": str}
        , json={}
        , pkl={})

    d.txt["hi"],d.txt["bye"] = "hello","goodbye"
    d.py["hi"],d.py["hihi"],d.py["hihihi"] = "hello_1","hello_2","hello_3"
    for i in range(1, 5):
        d.json[str(i)] = i
    for i in range(1, 10):
        d.pkl[str(i)] = i*i

    assert d.txt["hi"] == "hello"
    assert d.txt["bye"] == "goodbye"
    assert d.py["hi"] == "hello_1"
    assert d.py["hihi"] == "hello_2"
    assert d.py["hihihi"] == "hello_3"
    for i in range(1, 5):
        assert d.json[str(i)] == i
    for i in range(1, 10):
        assert d.pkl[str(i)] == i*i

    assert len(d.txt) == 2
    assert len(d.py) == 3
    assert len(d.json) == 4
    assert len(d.pkl) == 9