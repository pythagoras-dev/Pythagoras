import pythagoras as pth
from pythagoras._05_mission_control.global_state_management import _clean_global_state


def test_local_initialization(tmp_path):
    _clean_global_state()

    init_params = dict(
        cloud_type="local",base_dir=tmp_path, default_island_name="kuku")

    pth.initialize(**init_params)

    assert pth.is_global_state_correct()
    assert pth.is_correctly_initialized()

    assert pth.initialization_parameters == init_params
    assert len(pth.value_store) == 0
    assert len(pth.crash_history) == 0
    assert pth.default_island_name == "kuku"

def test_corrupt_value_store(tmp_path):
    _clean_global_state()
    init_params = dict(
        cloud_type="local", base_dir=tmp_path, default_island_name="kuku")

    pth.initialize(**init_params)
    pth.value_store = None
    assert not pth.is_global_state_correct()
    assert not pth.is_correctly_initialized()
    assert not pth.is_unitialized()

def test_corrupt_crash_history(tmp_path):
    _clean_global_state()
    init_params = dict(
        cloud_type="local", base_dir=tmp_path, default_island_name="kuku")

    pth.initialize(**init_params)
    pth.crash_history = 42
    assert not pth.is_global_state_correct()
    assert not pth.is_correctly_initialized()
    assert not pth.is_unitialized()

def test_corrupt_cloudized_functions(tmp_path):
    _clean_global_state()
    init_params = dict(
        cloud_type="local", base_dir=tmp_path, default_island_name="kuku")

    pth.initialize(**init_params)
    pth.idempotent_functions = "To be, or not to be, that is the question"
    assert not pth.is_global_state_correct()
    assert not pth.is_correctly_initialized()
    assert not pth.is_unitialized()

def test_corrupt_island_name(tmp_path):
    _clean_global_state()
    init_params = dict(
        cloud_type="local", base_dir=tmp_path, default_island_name="kuku")

    pth.initialize(**init_params)
    pth.default_island_name = "new name"
    assert not pth.is_global_state_correct()
    assert not pth.is_correctly_initialized()
    assert not pth.is_unitialized()