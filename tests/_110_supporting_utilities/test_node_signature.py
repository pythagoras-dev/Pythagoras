import os
import sys
import tempfile
from pythagoras._110_supporting_utilities.node_signature import (
    get_node_signature, _is_non_trivial_id, _read_first, _run
)
from pythagoras._110_supporting_utilities import PTH_BASE32_ALPHABET


def test_get_node_signature_structure():
    """Test the structure of the node signature."""
    sig = get_node_signature()
    
    assert isinstance(sig, str)
    assert len(sig) > 8, "Signature should have at least 8 characters"
    assert all(c in PTH_BASE32_ALPHABET for c in sig), f"Signature contains invalid characters: {sig}"
    assert sig != "signatureless_node_signatureless", "Node signature generation failed completely"

def test_get_node_signature_determinism():
    """Test that get_node_signature returns the same value on subsequent calls."""
    sig1 = get_node_signature()
    sig2 = get_node_signature()
    
    assert sig1 == sig2, "Node signature should be deterministic"

def test_get_node_signature_is_not_empty():
    """Test that the signature is not empty/None."""
    sig = get_node_signature()
    assert sig is not None
    assert sig != ""

def test_is_non_trivial_id():
    # Basic valid cases
    assert _is_non_trivial_id("abc") == "abc"
    assert _is_non_trivial_id(" 123 ") == "123"
    assert _is_non_trivial_id("a-b-c") == "a-b-c"

    # Invalid/Trivial cases
    assert _is_non_trivial_id(None) is None
    assert _is_non_trivial_id("") is None
    assert _is_non_trivial_id("   ") is None
    assert _is_non_trivial_id("0000") is None
    assert _is_non_trivial_id("ffff") is None
    assert _is_non_trivial_id("00-00-00") is None
    assert _is_non_trivial_id("{}") is None
    assert _is_non_trivial_id("---") is None

def test_read_first():
    # Test reading existing file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test_content")
        f_path = f.name

    try:
        assert _read_first(f_path) == "test_content"
    finally:
        os.remove(f_path)

    # Test reading non-existent file
    assert _read_first("/non/existent/path/to/file") is None

def test_run_command():
    # Test valid command
    cmd = [sys.executable, "-c", "print('hello')"]
    output = _run(cmd)
    assert output == "hello"

    # Test invalid command
    output = _run(["invalid_command_that_does_not_exist_12345"])
    assert output is None
