from persidict import replace_unsafe_chars

from pythagoras import (
    convert_base16_to_base32,
    convert_base32_to_int,
    convert_int_to_base32,
)


def test_round_trip_int_to_base32_to_int():
    """Test round-trip conversion: int -> base32 -> int."""
    test_values = [0, 1, 10, 31, 32, 100, 255, 1000, 32768, 1000000]
    for val in test_values:
        base32_str = convert_int_to_base32(val)
        result = convert_base32_to_int(base32_str)
        assert result == val


def test_round_trip_hex_to_base32_to_int_small_range():
    """Test round-trip conversion for small range: hex -> base32 -> int."""
    for i in range(1000):
        i_base16 = hex(i)[2:]
        i_base32 = convert_base16_to_base32(i_base16)
        # Verify base32 string is filesystem-safe
        assert i_base32 == replace_unsafe_chars(i_base32, replace_with="_")
        i_new = convert_base32_to_int(i_base32)
        assert i_new == i


def test_round_trip_hex_to_base32_to_int_large_range():
    """Test round-trip conversion for large range: hex -> base32 -> int."""
    max_val = 100_000_000_000_000_000_000
    max_val *= max_val * max_val
    max_val *= max_val * max_val
    max_val *= max_val * max_val
    step = max_val // 1000
    for i in range(0, max_val, step):
        i_base16 = hex(i)[2:]
        i_base32 = convert_base16_to_base32(i_base16)
        # Verify base32 string is filesystem-safe
        assert i_base32 == replace_unsafe_chars(i_base32, replace_with="_")
        i_new = convert_base32_to_int(i_base32)
        assert i_new == i
