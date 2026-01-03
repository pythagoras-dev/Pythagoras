import pytest

from pythagoras import convert_base16_to_base32


def test_convert_base16_to_base32_basics():
    """Test basic hexadecimal to base32 conversions with known values."""
    assert convert_base16_to_base32("0") == "0"
    assert convert_base16_to_base32("1") == "1"
    assert convert_base16_to_base32("a") == "a"
    assert convert_base16_to_base32("1f") == "v"   # 31 in decimal
    assert convert_base16_to_base32("20") == "10"  # 32 in decimal
    assert convert_base16_to_base32("ff") == "7v"  # 255 in decimal


def test_convert_base16_to_base32_edge_cases():
    """Test edge cases for convert_base16_to_base32."""
    # Empty string -> "0"
    assert convert_base16_to_base32("") == "0"
    # Case insensitivity
    assert convert_base16_to_base32("FF") == convert_base16_to_base32("ff")
    assert convert_base16_to_base32("AbCdEf") == convert_base16_to_base32("abcdef")
    # Whitespace handling
    assert convert_base16_to_base32("  ff  ") == convert_base16_to_base32("ff")


def test_convert_base16_to_base32_errors():
    """Test error handling for convert_base16_to_base32."""
    # Invalid hexadecimal characters
    with pytest.raises(ValueError, match="Invalid hexadecimal string"):
        convert_base16_to_base32("zz")

    with pytest.raises(ValueError, match="Invalid hexadecimal string"):
        convert_base16_to_base32("gg")
