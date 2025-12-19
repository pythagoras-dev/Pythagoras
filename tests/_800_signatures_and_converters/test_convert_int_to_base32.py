import pytest

from pythagoras import convert_int_to_base32


def test_convert_int_to_base32_basics():
    """Test basic integer to base32 conversions."""
    # Test 0
    assert convert_int_to_base32(0) == "0"
    # Test small numbers
    assert convert_int_to_base32(1) == "1"
    assert convert_int_to_base32(10) == "a"
    assert convert_int_to_base32(31) == "v"
    assert convert_int_to_base32(32) == "10"
    assert convert_int_to_base32(33) == "11"


def test_convert_int_to_base32_powers_of_32():
    """Test powers of 32 for boundary values."""
    assert convert_int_to_base32(32) == "10"      # 32^1
    assert convert_int_to_base32(1024) == "100"   # 32^2
    assert convert_int_to_base32(32768) == "1000" # 32^3


def test_convert_int_to_base32_full_alphabet():
    """Test that all 32 characters in the alphabet are used correctly."""
    # Test each digit 0-9 and letter a-v (0-31 in decimal)
    expected_alphabet = "0123456789abcdefghijklmnopqrstuv"
    for i in range(32):
        result = convert_int_to_base32(i)
        assert result == expected_alphabet[i]


def test_convert_int_to_base32_errors():
    """Test error handling for convert_int_to_base32."""
    # Negative numbers
    with pytest.raises(ValueError, match="n must be non-negative"):
        convert_int_to_base32(-1)

    # Wrong type: float
    with pytest.raises(TypeError, match="n must be an int"):
        convert_int_to_base32(1.5) # type: ignore

    # Wrong type: string
    with pytest.raises(TypeError, match="n must be an int"):
        convert_int_to_base32("10") # type: ignore
