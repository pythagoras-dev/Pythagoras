import uuid, platform, getpass
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
    mac = uuid.getnode()
    system = platform.system()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    processor = platform.processor()
    user = getpass.getuser()
    id_string = f"{mac}{system}{release}{version}"
    id_string += f"{machine}{processor}{user}"
    return get_hash_signature(id_string)