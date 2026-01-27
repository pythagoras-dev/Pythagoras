import pytest


def test_version_fallback_to_unknown(monkeypatch):
    # Patch importlib.metadata.version to raise PackageNotFoundError
    import importlib.metadata as md
    import sys

    def _raise(_name):
        raise md.PackageNotFoundError

    # Remove modules from cache to force fresh import
    sys.modules.pop('pythagoras._version_info', None)
    sys.modules.pop('pythagoras', None)

    monkeypatch.setattr(md, "version", _raise, raising=True)

    # Import with patched metadata.version
    import pythagoras

    assert hasattr(pythagoras, "__version__")
    assert pythagoras.__version__ == "unknown"

    # Clean up: remove modules from cache so subsequent tests get fresh imports
    sys.modules.pop('pythagoras._version_info', None)
    sys.modules.pop('pythagoras', None)

    # Monkeypatch will auto-revert when this function exits


@pytest.fixture(autouse=True, scope="function")
def cleanup_pythagoras_module():
    """Ensure pythagoras module is cleaned up after each test in this file."""
    yield
    # After each test, remove pythagoras from cache to prevent pollution
    import sys
    sys.modules.pop('pythagoras._version_info', None)
    sys.modules.pop('pythagoras', None)
