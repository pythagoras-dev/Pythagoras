import os
from urllib.parse import urlparse

from .._090_swarming_portals import SwarmingPortal


def _is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def _is_valid_folder_name(path_str):
    if os.path.isdir(path_str):
        return True
    try:
        os.makedirs(path_str, exist_ok=True)
        return True
    except OSError:
        return False

def get_portal(url_or_foldername:str) -> SwarmingPortal:
    """Create a return a portal object based on a URL or a directory.   """
    if _is_valid_folder_name(url_or_foldername):
        return SwarmingPortal(url_or_foldername)
    elif _is_valid_url(url_or_foldername):
        raise NotImplementedError("URLы not supported yet ... stay turned")
    else:
        raise ValueError(f"Invalid folder name: {url_or_foldername}")