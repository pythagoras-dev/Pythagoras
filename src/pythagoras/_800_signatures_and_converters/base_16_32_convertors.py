from typing import Final

_BASE32_ALPHABET: Final[str] = '0123456789abcdefghijklmnopqrstuv'
_BASE32_ALPHABET_MAP: Final[dict[str, int]] = {
    char:index for index,char in enumerate(_BASE32_ALPHABET)}


def convert_base16_to_base32(hexdigest: str) -> str:
    """Convert a hexadecimal (base16) string to this project's base32.

    Args:
        hexdigest (str): A hexadecimal string (case-insensitive). May be an
            empty string or "0" to represent zero.

    Returns:
        str: The corresponding value encoded with the custom base32 alphabet
        (digits 0-9 then letters a-v).

    Examples:
        >>> convert_base16_to_base32("ff")
        '7v'
    """

    try:
        num = int(hexdigest, 16)
    except ValueError as e:
        raise ValueError(f"Invalid hexadecimal string: {hexdigest}") from e

    base32_str = convert_int_to_base32(num)

    return base32_str


def convert_int_to_base32(n: int) -> str:
    """Convert a non-negative integer to Pythagoras' base32 string.

    Args:
        n (int): Non-negative integer to encode.

    Returns:
        str: The base32 representation.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    if n == 0:
        return "0"

    base32_str = ''
    while n > 0:
        base32_str = _BASE32_ALPHABET[n & 31] + base32_str
        n >>= 5

    return base32_str

def convert_base_32_to_int(digest: str) -> int:
    """Convert a base32 string (custom alphabet) to an integer.

    Args:
        digest (str): String encoded with Pythagoras' base32 alphabet.

    Returns:
        int: The decoded non-negative integer value.

    Raises:
        KeyError: If digest contains a character outside the supported
            base32 alphabet (0-9, a-v).
    """
    if not digest:
        raise ValueError("Digest cannot be empty")

    digest = digest.lower()
    num = 0
    try:
        for char in digest:
            num = num * 32 + _BASE32_ALPHABET_MAP[char]
    except KeyError as e:
        raise ValueError(f"Invalid character '{e.args[0]}' in base32 digest: {digest}") from e
    return num

