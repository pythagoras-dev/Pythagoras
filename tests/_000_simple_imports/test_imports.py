def test_import_pythagoras():
    """Test that pythagoras can be imported successfully."""
    import pythagoras
    assert pythagoras is not None


def test_import_protected_code_portals():
    """Test that protected code portals can be imported without pynvml."""
    from pythagoras._070_protected_code_portals import (
        get_unused_ram_mb,
        get_unused_cpu_cores,
        get_unused_nvidia_gpus,
    )
    # Verify the imports succeeded and functions are callable
    assert callable(get_unused_ram_mb)
    assert callable(get_unused_cpu_cores)
    assert callable(get_unused_nvidia_gpus)

