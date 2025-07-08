import uuid, platform, getpass
from functools import cache

from .hash_signatures import get_hash_signature


@cache
def get_node_signature() -> str:
    """Returns a globally-unique signature for the current computing node.
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