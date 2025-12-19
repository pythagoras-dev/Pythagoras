import string
from typing import Final

# Reusable, module-level constants
BASE32_ALPHABET: Final[str] = string.digits + string.ascii_lowercase[:22]
BASE32_ALLOWED: Final[set[str]] = set(BASE32_ALPHABET)


def convert_base16_to_base32(hexdigest: str) -> str:
    """Convert a hexadecimal (base16) string to this project's base32.

    Args:
        hexdigest (str): A hexadecimal string (case-insensitive). May be an
            empty string or "0" to represent zero.

    Returns:
        str: The corresponding value encoded with the base32 alphabet
        (digits 0-9 then letters a-v).

    Examples:
        >>> convert_base16_to_base32("ff")
        '7v'
    """
    hexdigest = hexdigest.strip().lower()
    if not hexdigest:
        return "0"

    try:
        num = int(hexdigest, 16)
    except ValueError as e:
        raise ValueError(f"Invalid hexadecimal string: {hexdigest}") from e

    base32_str = convert_int_to_base32(num)

    return base32_str


def convert_int_to_base32(n: int) -> str:
    """Convert a non-negative integer to base-32 alphabet (0-9 a-v)."""
    if not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return "0"

    out: list[str] = []
    while n:
        out.append(BASE32_ALPHABET[n & 31])  # last 5 bits
        n >>= 5
    out.reverse()
    return "".join(out)


def convert_base32_to_int(digest: str) -> int:
    """Convert a base-32 string (0-9 a-v) to an integer."""
    digest = digest.strip().lower()
    if not digest:
        return 0
    invalid = set(digest) - BASE32_ALLOWED
    if invalid:
        raise ValueError(
            f"Invalid base32 digit(s): {''.join(sorted(invalid))!r}. "
            f"Valid characters: {BASE32_ALPHABET}")
    # int() is now safe
    return int(digest, 32)

