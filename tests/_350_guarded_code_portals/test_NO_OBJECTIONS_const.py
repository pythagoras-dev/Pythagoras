from pythagoras import NoObjectionsFlag, NO_OBJECTIONS

def test_NoObjectionsFlag():
    """Test if NoObjectionsFlag is a singleton.
    """
    assert NO_OBJECTIONS is NoObjectionsFlag()
    instance_1 = NoObjectionsFlag()
    assert NO_OBJECTIONS is instance_1
