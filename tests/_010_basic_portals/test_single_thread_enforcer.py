import threading
import pytest
import pythagoras._010_basic_portals.single_thread_enforcer as ste
from pythagoras._010_basic_portals.single_thread_enforcer import (
    _ensure_single_thread,
    _reset_single_thread_enforcer,
)

def setup_function():
    """Reset the enforcer before each test."""
    _reset_single_thread_enforcer()

def teardown_function():
    """Reset the enforcer after each test."""
    _reset_single_thread_enforcer()

def test_single_thread_success():
    """Test that the first thread to access can access repeatedly."""
    # First access
    _ensure_single_thread()
    assert ste._portal_native_id == threading.get_native_id()
    
    # Second access from same thread
    _ensure_single_thread()
    assert ste._portal_native_id == threading.get_native_id()

def test_multi_thread_failure():
    """Test that a second thread raises RuntimeError."""
    # Main thread claims ownership
    _ensure_single_thread()
    
    exception_caught = False
    
    def intruder_thread():
        nonlocal exception_caught
        try:
            _ensure_single_thread()
        except RuntimeError as e:
            if "Pythagoras portals are single-threaded by design" in str(e):
                exception_caught = True

    t = threading.Thread(target=intruder_thread, name="Intruder")
    t.start()
    t.join()
    
    assert exception_caught, "Secondary thread should have raised RuntimeError"

def test_reset_allows_new_owner():
    """Test that resetting allows a new thread to become the owner."""
    # Main thread claims ownership
    _ensure_single_thread()
    
    # Reset
    _reset_single_thread_enforcer()
    assert ste._portal_native_id is None
    
    # New thread attempts to claim ownership
    exception_caught = False
    
    def new_owner_thread():
        nonlocal exception_caught
        try:
            _ensure_single_thread()
        except Exception:
            exception_caught = True

    t = threading.Thread(target=new_owner_thread, name="NewOwner")
    t.start()
    t.join()
    
    assert not exception_caught, "New thread should succeed after reset"
    
    # Now main thread should fail because "NewOwner" claimed it
    # Note: "NewOwner" thread finished, but the enforcer remembers the ID.
    # The ID might be reused by OS, but likely not immediately. 
    # Even if "NewOwner" is dead, the enforcer still holds its ID.
    
    # However, if threading.get_native_id() of the main thread is different 
    # from the stored ID (which was NewOwner's ID), it should raise RuntimeError.
    
    with pytest.raises(RuntimeError) as excinfo:
        _ensure_single_thread()
    
    assert "Pythagoras portals are single-threaded by design" in str(excinfo.value)
