import time

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._040_logging_code_portals import (
    LoggingCodePortal, logging)

def two_arg_function_original(a: int, b: int) -> int:
    print(f"Hello, world! {a=} {b=} {a+b=}")
    return a + b

def test_2args_function_single_call(tmpdir):
    # tmpdir = "TWO_ARGS_FUNCTION_SINGLE_CALL_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:

        two_arg_function = logging(excessive_logging=True)(two_arg_function_original)

        two_arg_function(a=1, b=2)

        assert p.portal.get_number_of_linked_functions() == 0
        # two_arg_function.portal = p.portal
        # assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal._value_store) == 6

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 1
        assert len(p.portal._run_history.pkl) == 1
        assert len(p.portal._run_history.txt) == 1
        assert len(p.portal._run_history.json) == 1



def test_2args_function_2similar_calls(tmpdir):
    # tmpdir = "TWO_ARGS_FUNCTION_2SIMILAR_CALLS_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global two_arg_function
        two_arg_function = logging(
            excessive_logging=True
            , portal=p.portal
            )(two_arg_function_original)

        two_arg_function(a=1, b=2)
        two_arg_function(b=2, a=1)

        assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal._value_store) == 6

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 1
        assert len(p.portal._run_history.pkl) == 2
        assert len(p.portal._run_history.txt) == 2
        assert len(p.portal._run_history.json) == 2

def test_2args_function_2different_calls(tmpdir):
    # tmpdir = "TWO_ARGS_FUNCTION_2DIFFERENT_CALLS_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global two_arg_function
        two_arg_function = logging(
            excessive_logging=True
            , portal = p.portal
            )(two_arg_function_original)

        two_arg_function(a=1, b=2)
        two_arg_function(a=1, b=10)

        assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal._value_store) == 10

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 2
        assert len(p.portal._run_history.pkl) == 2
        assert len(p.portal._run_history.txt) == 2
        assert len(p.portal._run_history.json) == 2

def test_2args_function_single_call_no_logs(tmpdir):
    # tmpdir = "TWO_ARGS_FUNCTION_SINGLE_CALL_NO_LOGS_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global two_arg_function
        two_arg_function = logging(excessive_logging=False,portal = p.portal)(two_arg_function_original)

        two_arg_function(a=1, b=2)

        assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal._value_store) == 5

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 0
        assert len(p.portal._run_history.pkl) == 0
        assert len(p.portal._run_history.txt) == 0
        assert len(p.portal._run_history.json) == 0

def test_2args_function_2similar_calls_no_logs(tmpdir):
    # tmpdir = "TWO_ARGS_FUNCTION_2SIMILAR_CALLS_NO_LOGS_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global two_arg_function
        two_arg_function = logging(excessive_logging=False,portal = p.portal)(two_arg_function_original)

        two_arg_function(a=1, b=2)
        two_arg_function(b=2, a=1)

        assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal._value_store) == 5

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 0
        assert len(p.portal._run_history.pkl) == 0
        assert len(p.portal._run_history.txt) == 0
        assert len(p.portal._run_history.json) == 0

def test_2args_function_2different_calls_no_logs(tmpdir):
    # tmpdir = "TWO_ARGS_FUNCTION_2DIFFERENT_CALLS_NO_LOGS_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global two_arg_function
        two_arg_function = logging(excessive_logging=False,portal = p.portal)(two_arg_function_original)

        two_arg_function(a=1, b=2)
        two_arg_function(a=1, b=10)

        assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal._value_store) == 8

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 0
        assert len(p.portal._run_history.pkl) == 0
        assert len(p.portal._run_history.txt) == 0
        assert len(p.portal._run_history.json) == 0

