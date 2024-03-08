from pythagoras._05_events_and_exceptions.type_retrievers import (
    retrieve_IdempotentFunction_class
    , retrieve_AutonomousFunction_class
    , retrieve_FunctionExecutionResultAddress_class
    , retrieve_FunctionExecutionContext_class)


import pythagoras as pth

def test_type_retrievers():
    assert retrieve_IdempotentFunction_class() == pth.IdempotentFunction
    assert retrieve_AutonomousFunction_class() == pth.AutonomousFunction
    assert retrieve_FunctionExecutionResultAddress_class(
        ) == pth.FunctionExecutionResultAddress
    assert retrieve_FunctionExecutionContext_class(
        ) == pth.FunctionExecutionContext
