import pytest

from pythagoras import convert_base32_to_int


def test_convert_base32_to_int_basics():
    """Test basic base32 to integer conversions."""
    assert convert_base32_to_int("0") == 0
    assert convert_base32_to_int("1") == 1
    assert convert_base32_to_int("a") == 10
    assert convert_base32_to_int("v") == 31
    assert convert_base32_to_int("10") == 32
    assert convert_base32_to_int("11") == 33


def test_convert_base32_to_int_edge_cases():
    """Test edge cases for convert_base32_to_int."""
    # Empty string -> 0
    assert convert_base32_to_int("") == 0
    # Case insensitivity
    val = convert_base32_to_int("7v")
    assert convert_base32_to_int("7V") == val
    # Whitespace handling
    assert convert_base32_to_int("  7v  ") == val


def test_convert_base32_to_int_errors():
    """Test error handling for convert_base32_to_int."""
    # Invalid character 'w' (not in 0-9a-v)
    with pytest.raises(ValueError, match="Invalid base32 digit"):
        convert_base32_to_int("w")

    # Invalid character '!'
    with pytest.raises(ValueError, match="Invalid base32 digit"):
        convert_base32_to_int("7!")
