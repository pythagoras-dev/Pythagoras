import string


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
    """Convert a non-negative integer to base-32 alphabet (0-9 a-v).

    Args:
        n: Non-negative integer to encode.

    Returns:
        The base-32 representation.

    Raises:
        ValueError: If *n* is negative.
        TypeError:  If *n* is not an ``int``.
    """
    if not isinstance(n, int):
        raise TypeError(f"n must be int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return "0"


    out: list[str] = []
    alphabet = string.digits + string.ascii_lowercase[:22]
    append = out.append
    while n:
        append(alphabet[n & 31])  # grab the last 5 bits
        n >>= 5

    # Reverse once at the end to obtain the most-significant-first order.
    out.reverse()
    return "".join(out)


def convert_base32_to_int(digest: str) -> int:
    """Convert a base32 string (0-9 a-v) to an integer.

    Args:
        digest (str): String encoded with case-insensitive base32 alphabet.

    Returns:
        int: The decoded non-negative integer value.

    Raises:
        ValueError: If digest contains a character outside the supported
            base32 alphabet (0-9 a-v).
    """
    digest = digest.strip().lower()
    if not digest:
        return 0

    try:
        return int(digest, 32)
    except ValueError as e:
        raise ValueError(f"Invalid base32 digest: {digest}") from e

