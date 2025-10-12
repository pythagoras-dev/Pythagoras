import getpass
import platform
import uuid
from functools import cache

from .hash_signatures import get_hash_signature


@cache
def get_node_signature() -> str:
    """Return a stable signature for the current computing node and user.

    The signature is derived from a concatenation of multiple system- and
    user-specific attributes (MAC address, OS info, CPU, username) and then
    hashed using Pythagoras' short base32 digest. The result is intended to
    uniquely identify the node within logs and distributed systems.

    Caching:
        The result is cached for the lifetime of the process using
        functools.cache, as the underlying attributes are not expected to
        change while the process is running.

    Returns:
        str: A short base32 signature string representing this node.
    """
    id_parts = [
        str(uuid.getnode()),
        platform.system(),
        platform.release(),
        platform.version(),
        platform.machine(),
        platform.processor(),
        getpass.getuser(),
    ]
    return get_hash_signature("".join(id_parts))