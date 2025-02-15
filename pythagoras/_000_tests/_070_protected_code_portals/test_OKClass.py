from pythagoras import OKClass, OK

def test_OKClass():
    """Test if OKClass is a singleton.
    """
    assert OK is OKClass()
    OK_1 = OKClass()
    assert OK is OK_1