from typing import Dict, Any


def sort_dict_by_keys(d:Dict[str,Any]) -> Dict[str,Any]:
    """Sort a dictionary by its keys."""
    assert isinstance(d, dict)
    return {k: d[k] for k in sorted(d.keys())}