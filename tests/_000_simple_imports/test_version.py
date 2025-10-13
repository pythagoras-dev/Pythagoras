from importlib import metadata as md


def test_version_matches_metadata():
    import pythagoras
    assert pythagoras.__version__ == md.version("pythagoras")
