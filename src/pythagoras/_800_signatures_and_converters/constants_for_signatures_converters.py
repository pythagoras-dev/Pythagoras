"""
Constants and configuration parameters for signatures and converters.
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

PTH_METADATA_TIMEOUT: float = 2
# Timeout (in seconds) for external metadata requests (e.g. cloud provider APIs).

PTH_METADATA_READ_LIMIT: int = 4096
# Maximum bytes to read from files or sockets to prevent memory issues
# with pathological inputs.

PTH_APP_NAME: str = "pythagoras"
# Application namespace used for creating system or user-level config directories.

SMBIOS_UUID_PATH: str = "/sys/class/dmi/id/product_uuid"
# Location of the hardware product UUID on Linux systems.

PTH_NODE_SIGNATURE_VERSION: str = "version 2"
# Version string prepended to node signatures to support future algorithm evolution.
