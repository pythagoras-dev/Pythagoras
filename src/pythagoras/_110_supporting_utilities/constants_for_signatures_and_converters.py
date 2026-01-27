"""Constants used by signature and base-conversion utilities.

This module centralises tunables that affect how identifiers are formed and
encoded. Changing values here affects the entire subpackage.

Key choices:
- ``PTH_MAX_SIGNATURE_LENGTH``: Truncation length for short, human/URL-friendly
  signatures. With base32 (5 bits/char), ``22`` chars ≈ 110 bits — ample for
  practical collision resistance while staying compact.
- ``PTH_BASE32_ALPHABET``: Project-specific alphabet (``0-9`` then ``a-v``),
  intentionally different from RFC 4648; used consistently for encoding/decoding.
- ``PTH_HASH_TYPE``: Hash algorithm name used by joblib hashing helpers.
"""
from __future__ import annotations

import string
from typing import Final

PTH_MAX_SIGNATURE_LENGTH: Final[int] = 22
# 22 characters provides ~110 bits of entropy (5 bits per base32 char),
# sufficient for collision resistance in typical use cases.
# Must be at least 7 to support HashAddr shard/subshard slicing.

PTH_HASH_TYPE: Final[str] = "sha256"

PTH_BASE32_ALPHABET: Final[str] = string.digits + string.ascii_lowercase[:22]
PTH_BASE32_ALLOWED: Final[set[str]] = set(PTH_BASE32_ALPHABET)

PTH_METADATA_TIMEOUT: Final[float] = 2
# Timeout (seconds) for metadata/OS calls where applicable.

PTH_METADATA_READ_LIMIT: Final[int] = 4096
# Max bytes to read from files/sockets to avoid pathological memory use.

PTH_APP_NAME: Final[str] = "pythagoras"
# Namespace used for system/user-level config directories.

SMBIOS_UUID_PATH: Final[str] = "/sys/class/dmi/id/product_uuid"
# Hardware product UUID path on Linux systems.

PTH_NODE_SIGNATURE_VERSION: Final[str] = "version_2"
# Version tag mixed into node-signature payload (enables future evolution).
