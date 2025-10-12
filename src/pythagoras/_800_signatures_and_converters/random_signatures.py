import uuid
from typing import Final

from .base_16_32_convertors import convert_int_to_base32

_MAX_SIGNATURE_LENGTH: Final[int] = 22

def get_random_signature() -> str:
    """Generate a short, random base32 signature string.

    The randomness is sourced from uuid.uuid4(), which uses a cryptographically
    strong RNG provided by the OS. The resulting large integer is encoded with
    Pythagoras' base32 alphabet and truncated to max_signature_length
    characters.

    Returns:
        str: A random, URL-safe base32 string of length up to
        max_signature_length.
    """
    random_int = uuid.uuid4().int
    random_str = convert_int_to_base32(random_int)
    return random_str[:_MAX_SIGNATURE_LENGTH]
