from src.pythagoras._010_basic_portals import NotPicklable

import pytest

def test_not_picklable():
    npo = NotPicklable()
    with pytest.raises(TypeError, match="NotPicklable cannot be pickled"):
        _ = npo.__getstate__()

    with pytest.raises(TypeError, match="NotPicklable cannot be unpickled"):
        npo.__setstate__({"key": "value"})