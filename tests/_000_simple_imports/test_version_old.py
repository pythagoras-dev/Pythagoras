

def test_version_matches_metadata():
    from importlib import metadata
    import pythagoras
    assert pythagoras.__version__ == metadata.version("pythagoras")


def test_version_exists():
    """Test that __version__ attribute exists."""
    import pythagoras
    assert hasattr(pythagoras, '__version__')


def test_version_is_string():
    """Test that __version__ is a string."""
    import pythagoras
    assert isinstance(pythagoras.__version__, str)


def test_version_not_empty():
    """Test that __version__ is not empty."""
    import pythagoras
    assert len(pythagoras.__version__) > 0


def test_version_format():
    """Test that __version__ follows semantic versioning format (X.Y.Z or X.Y.Z.something)."""
    import pythagoras
    import re
    version_pattern = r'^\d+\.\d+\.\d+(?:\.\w+|\w+\d*)?$'
    assert re.match(version_pattern, pythagoras.__version__), f"Version '{pythagoras.__version__}' does not match expected format"


def test_version_accessible():
    """Test that __version__ can be accessed and printed."""
    import pythagoras
    version = pythagoras.__version__
    assert version is not None
    # Should not raise any exceptions when converted to string
    str_version = str(version)
    assert len(str_version) > 0