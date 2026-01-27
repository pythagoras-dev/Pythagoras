"""Converters between base16 (hex), base32, and integer representations.

Notes:
- Uses a custom base32 alphabet: digits ``0-9`` followed by letters ``a-v``
  (32 chars). This differs from RFC 4648 base32 and is chosen for compact,
  URL‑safe identifiers.
- Conversions are numeric: leading zeros are not preserved when converting
  between textual bases; zero is represented as the single character ``"0"``.
"""

from .constants_for_signatures_and_converters import PTH_BASE32_ALLOWED
from .constants_for_signatures_and_converters import PTH_BASE32_ALPHABET
from .long_infoname import get_long_infoname


def convert_base16_to_base32(hexdigest: str) -> str:
    """Convert a hexadecimal (base16) string to this project's base32.

    Args:
        hexdigest: A hexadecimal string (case-insensitive). May be an
            empty string or "0" to represent zero.

    Returns:
        The corresponding value encoded with the base32 alphabet
        (digits 0-9 then letters a-v).

    Raises:
        ValueError: If ``hexdigest`` is not a valid hexadecimal string.

    Example:
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
    """Convert a non-negative integer to a base-32 string (0-9 a-v).

    Args:
        n: The integer to convert. Must be non-negative.

    Returns:
        The base-32 string representation of the integer.

    Raises:
        TypeError: If n is not an integer.
        ValueError: If n is negative.
    """
    if not isinstance(n, int):
        raise TypeError(f"n must be an int, got {get_long_infoname(n)}")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return "0"

    out: list[str] = []
    while n:
        out.append(PTH_BASE32_ALPHABET[n & 31])
        n >>= 5
    out.reverse()
    return "".join(out)


def convert_base32_to_int(digest: str) -> int:
    """Convert a base-32 string (0-9 a-v) to an integer.

    Args:
        digest: The base-32 string to convert. Case-insensitive.

    Returns:
        The integer value of the base-32 string. Empty or
        whitespace-only input yields ``0``.

    Raises:
        ValueError: If the string contains invalid characters.
    """
    digest = digest.strip().lower()
    if not digest:
        return 0
    invalid = set(digest) - PTH_BASE32_ALLOWED
    if invalid:
        raise ValueError(
            f"Invalid base32 digit(s): {''.join(sorted(invalid))!r}. "
            f"Valid characters: {PTH_BASE32_ALPHABET}")
    
    return int(digest, 32)

