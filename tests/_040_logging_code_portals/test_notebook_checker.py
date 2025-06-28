from pythagoras._040_logging_code_portals.notebook_checker import is_executed_in_notebook

def test_is_executed_in_notebook():
    assert is_executed_in_notebook() == False
    #TODO: add test for when running inside a notebook
