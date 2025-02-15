from __future__ import annotations

import time

from deepdiff import DeepDiff
from persidict import PersiDict
import random

from persidict.persi_dict import PersiDictKey

from pythagoras._010_basic_portals import InconsistentChangeOfImmutableItem
from pythagoras._820_strings_signatures_converters import get_hash_signature


class FirstEntryDict(PersiDict):
    """ A dictionary that always keeps the first value assigned to a key.
    """
    _wrapped_dict: PersiDict
    _p_consistency_checks: float | None
    _total_checks_count: int
    _successful_checks_count: int

    def __init__(self
                 , wrapped_dict:PersiDict
                 , p_consistency_checks: float | None=None):
        assert isinstance(wrapped_dict, PersiDict)
        assert wrapped_dict.immutable_items == True
        assert p_consistency_checks is None or (0 <= p_consistency_checks <= 1)
        super().__init__(
            base_class_for_values=wrapped_dict.base_class_for_values
            ,immutable_items=True
            ,digest_len=wrapped_dict.digest_len)
        self._wrapped_dict = wrapped_dict
        self._p_consistency_checks = p_consistency_checks
        self._successful_checks_count = 0
        self._total_checks_count = 0

    def __setitem__(self, key, value):
        """ Set the value of a key if it is not already set.

        If the key is already set, it checks the value
        against the value that was first set.
        """
        check_needed = False

        try: # extra protections to better handle concurrent writes
            if key in self._wrapped_dict:
                check_needed = True
            else:
                self._wrapped_dict[key] = value
        except:
            time.sleep(random.random()/random.randint(1,5))
            if key in self._wrapped_dict:
                check_needed = True
            else:
                self._wrapped_dict[key] = value

        assert key in self._wrapped_dict

        if (check_needed
            and self._p_consistency_checks is not None
            and self._p_consistency_checks > 0):
            if random.random() < self._p_consistency_checks:
                self._total_checks_count += 1
                signature_old = get_hash_signature(self._wrapped_dict[key])
                signature_new = get_hash_signature(value)
                if signature_old != signature_new:
                    diff_dict = DeepDiff(self._wrapped_dict[key], value)
                    raise InconsistentChangeOfImmutableItem(
                        f"FirstEntryDict: key {key} is already set "
                        + f"to {self._wrapped_dict[key]} "
                        + f"and the new value {value} is different, "
                        + f"which is not allowed. Details here: {diff_dict} ")
                self._successful_checks_count += 1

    def __contains__(self, item):
        return item in self._wrapped_dict

    def __getitem__(self, key):
        return self._wrapped_dict[key]

    def __len__(self):
        return len(self._wrapped_dict)

    def _generic_iter(self, iter_type: str):
        return self._wrapped_dict._generic_iter(iter_type)

    def timestamp(self, key:PersiDictKey) -> float:
        return self._wrapped_dict.timestamp(key)

    def __getattr__(self, name):
        # Forward attribute access to the wrapped object
        return getattr(self._wrapped_dict, name)

    def get_subdict(self, prefix_key:PersiDictKey) -> FirstEntryDict:
        subdict = self._wrapped_dict.get_subdict(prefix_key)
        result = FirstEntryDict(subdict, self._p_consistency_checks)
        return result


