from pythagoras import ValidationSuccessClass, VALIDATION_SUCCESSFUL

def test_OKClass():
    """Test if OKClass is a singleton.
    """
    assert VALIDATION_SUCCESSFUL is ValidationSuccessClass()
    OK_1 = ValidationSuccessClass()
    assert VALIDATION_SUCCESSFUL is OK_1