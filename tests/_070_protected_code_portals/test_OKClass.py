from pythagoras import ValidationStatusClass, VALIDATION_SUCCESSFUL

def test_OKClass():
    """Test if OKClass is a singleton.
    """
    assert VALIDATION_SUCCESSFUL is ValidationStatusClass()
    OK_1 = ValidationStatusClass()
    assert VALIDATION_SUCCESSFUL is OK_1