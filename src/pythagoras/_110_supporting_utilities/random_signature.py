"""Cryptographically secure random signature generation.

We request ``PTH_MAX_SIGNATURE_LENGTH * 5`` random bits because each base32
character encodes 5 bits. This yields a uniformly random string of the target
length when encoded and truncated.
"""

import secrets

from .base_16_32_converters import convert_int_to_base32
from .constants_for_signatures_and_converters import PTH_MAX_SIGNATURE_LENGTH

def get_random_signature() -> str:
    """Generate a short, random base32 signature string.

    The randomness is sourced from secrets.randbits(), which uses a
    cryptographically strong RNG provided by the OS. The resulting large
    integer is encoded with Pythagoras' base32 alphabet and truncated to
    PTH_MAX_SIGNATURE_LENGTH characters.

    Returns:
        A random, URL-safe base32 string of length up to
        PTH_MAX_SIGNATURE_LENGTH.
    """
    random_int = secrets.randbits(PTH_MAX_SIGNATURE_LENGTH * 5)
    random_str = convert_int_to_base32(random_int)
    return random_str[:PTH_MAX_SIGNATURE_LENGTH]
