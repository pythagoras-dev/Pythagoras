"""Content-based hash signatures for arbitrary Python objects.

Provides functions to compute deterministic, stable hash signatures with
output in base16 (hex) or the project's base32 alphabet (``0-9`` then ``a-v``).
"""

from typing import Any

import joblib.hashing
import importlib.util

from .base_16_32_converters import convert_base16_to_base32
from .constants_for_signatures_and_converters import PTH_MAX_SIGNATURE_LENGTH, PTH_HASH_TYPE


def get_base16_hash_signature(x: Any) -> str:
    """Compute a hexadecimal (base16) hash for an arbitrary Python object.

    The implementation delegates to joblib's hashing utilities. If NumPy is
    importable, ``NumpyHasher`` is used (it knows how to hash arrays and falls
    back to generic behavior for other objects); otherwise the generic
    ``Hasher`` is used.

    Args:
        x: The object to hash. The object must be picklable.

    Returns:
        A hexadecimal digest computed with ``PTH_HASH_TYPE`` (``sha256``
        by default).

    Notes:
        - The digest is deterministic for the same object content.
        - joblib hashing operates on object content/structure, not memory
          addresses.
    """
    if importlib.util.find_spec("numpy"):
        hasher = joblib.hashing.NumpyHasher(hash_name=PTH_HASH_TYPE)
    else:
        hasher = joblib.hashing.Hasher(hash_name=PTH_HASH_TYPE)
    hash_signature = hasher.hash(x)
    return str(hash_signature)

def get_base32_hash_signature(x: Any) -> str:
    """Compute a base32-encoded hash for an arbitrary Python object.

    Internally computes a hexadecimal digest first, then converts it to the
    project's base32 alphabet (``0-9`` then ``a-v``).

    Args:
        x: The object to hash.

    Returns:
        The full-length base32 digest string (not truncated).
    """
    base_16_hash = get_base16_hash_signature(x)
    base_32_hash = convert_base16_to_base32(base_16_hash)
    return base_32_hash


def get_hash_signature(x: Any) -> str:
    """Compute a short, URL-safe hash signature for an object.

    Convenience wrapper returning the first ``PTH_MAX_SIGNATURE_LENGTH``
    characters of the base32 digest — typically sufficient for
    collision-resistant identifiers in logs and filenames.

    Args:
        x: The object to hash.

    Returns:
        The truncated base32 digest string.
    """
    return get_base32_hash_signature(x)[:PTH_MAX_SIGNATURE_LENGTH]

