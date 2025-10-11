import pickle

from pythagoras._010_basic_portals import NotPicklable

import pytest

# def test_not_picklable():
#     npo = NotPicklable()
#     with pytest.raises(TypeError, match="NotPicklable cannot be pickled"):
#         _ = npo.__getstate__()
#
#     with pytest.raises(TypeError, match="NotPicklable cannot be unpickled"):
#         npo.__setstate__({"key": "value"})


def test_not_picklable():
    npo = NotPicklable()

    # Test dunder methods directly
    with pytest.raises(TypeError):
        npo.__reduce__()
    with pytest.raises(TypeError):
        _ = npo.__getstate__()
    with pytest.raises(TypeError):
        npo.__setstate__({"key": "value"})

    # Test pickling via pickle.dumps(), which calls __reduce__()
    with pytest.raises(TypeError):
        pickle.dumps(npo)

    # Test that a subclass is also not picklable
    class MyNotPicklable(NotPicklable):
        pass
    mnpo = MyNotPicklable()
    with pytest.raises(TypeError):
        pickle.dumps(mnpo)