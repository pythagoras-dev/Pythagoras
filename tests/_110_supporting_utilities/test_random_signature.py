from persidict import replace_unsafe_chars

from pythagoras._110_supporting_utilities.constants_for_signatures_and_converters import (
    PTH_MAX_SIGNATURE_LENGTH, PTH_BASE32_ALPHABET)
from pythagoras._110_supporting_utilities.random_signature import (
    get_random_signature)

def test_random_id():
    all_random_ids = set()
    n_iterations = 10_000
    for i in range(n_iterations):
        random_id = get_random_signature()
        assert random_id == replace_unsafe_chars(random_id, replace_with="_")
        all_random_ids.add(random_id)
    assert len(all_random_ids) >= n_iterations-1


def test_signature_type():
    sig = get_random_signature()
    assert isinstance(sig, str)


def test_signature_length():
    for _ in range(100):
        sig = get_random_signature()
        assert len(sig) <= PTH_MAX_SIGNATURE_LENGTH
        assert len(sig) > 0


def test_signature_alphabet():
    for _ in range(100):
        sig = get_random_signature()
        for c in sig:
            assert c in PTH_BASE32_ALPHABET

