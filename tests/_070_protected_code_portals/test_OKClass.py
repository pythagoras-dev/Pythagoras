from pythagoras import ValidationSuccessFlag, VALIDATION_SUCCESSFUL

def test_OKClass():
    """Test if OKClass is a singleton.
    """
    assert VALIDATION_SUCCESSFUL is ValidationSuccessFlag()
    OK_1 = ValidationSuccessFlag()
    assert VALIDATION_SUCCESSFUL is OK_1