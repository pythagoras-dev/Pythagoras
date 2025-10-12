import sys
from typing import Any, Final

import joblib.hashing

from .base_16_32_convertors import convert_base16_to_base32


_HASH_TYPE: Final[str] = "sha256"
_MAX_SIGNATURE_LENGTH: Final[int] = 22

def get_base16_hash_signature(x:Any) -> str:
    """Compute a hexadecimal (base16) hash for an arbitrary Python object.

    This function delegates to joblib's hashing utilities. If NumPy is
    imported in the current process, it uses NumpyHasher for efficient and
    stable hashing of NumPy arrays; otherwise it uses the generic Hasher.

    Args:
        x (Any): The object to hash. Must be picklable by joblib unless a
            specialized routine (e.g., for NumPy arrays) is available.

    Returns:
        str: A hexadecimal string digest computed with the configured
            algorithm (sha256 by default).

    Notes:
        - joblib relies on pickle for most Python objects; ensure that custom
          objects are picklable for stable results.
        - The digest is deterministic for the same object content.
    """
    if 'numpy' in sys.modules:
        hasher = joblib.hashing.NumpyHasher(hash_name=_HASH_TYPE)
    else:
        hasher = joblib.hashing.Hasher(hash_name=_HASH_TYPE)
    hash_signature = hasher.hash(x)
    return str(hash_signature)

def get_base32_hash_signature(x:Any) -> str:
    """Compute a base32-encoded hash for an arbitrary Python object.

    Internally computes a hexadecimal digest first, then converts it to the
    custom base32 alphabet used by Pythagoras.

    Args:
        x (Any): The object to hash.

    Returns:
        str: The full-length base32 digest string (not truncated).
    """
    base_16_hash = get_base16_hash_signature(x)
    base_32_hash = convert_base16_to_base32(base_16_hash)
    return base_32_hash

def get_hash_signature(x:Any) -> str:
    """Compute a short, URL-safe hash signature for an object.

    This is a convenience wrapper that returns the first max_signature_length
    characters of the base32 digest, which is typically sufficient for
    collision-resistant identifiers in logs and filenames.

    Args:
        x (Any): The object to hash.

    Returns:
        str: The truncated base32 digest string.
    """
    return get_base32_hash_signature(x)[:_MAX_SIGNATURE_LENGTH]

