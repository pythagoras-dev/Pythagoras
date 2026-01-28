
from pythagoras import ValueAddr, LoggingFnCallSignature
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._320_logging_code_portals import (
    LoggingCodePortal, logging)

def simple_function_original():
    print("Hello, world!")


def test_simple_function_single_call_very_basic(tmpdir):
    # tmpdir = "SIMPLE_FUNCTION_SINGLE_CALL_VERY_BASIC_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            ) as p:
        for i in range(3):
            global simple_function
            simple_function = logging(excessive_logging=True, portal = p.portal)(simple_function_original)

            _addr = ValueAddr(simple_function)

            _signature = LoggingFnCallSignature(simple_function,dict())


            simple_function()

            assert p.portal.get_number_of_linked_functions() == 1

            assert len(p.portal.global_value_store) == 4

            assert len(p.portal._crash_history) == 0
            assert len(p.portal._event_history) == 0

            assert  len(p.portal._run_history.py) == 1
            assert len(p.portal._run_history.pkl) == i+1
            assert len(p.portal._run_history.txt) == i+1
            assert len(p.portal._run_history.json) == i+1


def test_simple_function_single_call(tmpdir):
    # tmpdir = "SIMPLE_FUNCTION_SINGLE_CALL_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        for i in range(3):
            global simple_function
            simple_function = logging(excessive_logging=True, portal = p.portal)(simple_function_original)

            simple_function()

            assert p.portal.get_number_of_linked_functions() == 1

            assert len(p.portal.global_value_store) == 4

            assert len(p.portal._crash_history) == 0
            assert len(p.portal._event_history) == 0

            assert  len(p.portal._run_history.py) == 1
            assert len(p.portal._run_history.pkl) == i+1
            assert len(p.portal._run_history.txt) == i+1
            assert len(p.portal._run_history.json) == i+1

def test_simple_function_single_call_no_logs(tmpdir):
    # tmpdir = "SIMPLE_FUNCTION_SINGLE_CALL_NO_LOGS_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            ) as p:
        global simple_function
        simple_function = logging(excessive_logging=False, portal = p.portal)(simple_function_original)

        simple_function()

        assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal.global_value_store) == 3

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 0
        assert len(p.portal._run_history.pkl) == 0
        assert len(p.portal._run_history.txt) == 0
        assert len(p.portal._run_history.json) == 0


def test_simple_function_double_call(tmpdir):
    # tmpdir = "SIMPLE_FUNCTION_DOUBLE_CALL_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        for i in range(1,5):
            global simple_function
            simple_function = logging(excessive_logging=True, portal = p.portal)(simple_function_original)

            simple_function()
            simple_function()

            assert p.portal.get_number_of_linked_functions() == 1

            assert len(p.portal.global_value_store) == 4

            assert len(p.portal._crash_history) == 0
            assert len(p.portal._event_history) == 0

            assert  len(p.portal._run_history.py) == 1
            assert len(p.portal._run_history.pkl) == 2*i
            assert len(p.portal._run_history.txt) == 2*i
            assert len(p.portal._run_history.json) == 2*i


def test_simple_function_double_call_no_logs(tmpdir):
    # tmpdir = "SIMPLE_FUNCTION_DOUBLE_CALL_NO_LOGS_"*2 + str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global simple_function
        simple_function = logging(excessive_logging=False, portal = p.portal)(simple_function_original)

        simple_function()
        simple_function()

        assert p.portal.get_number_of_linked_functions() == 1

        assert len(p.portal.global_value_store) == 3

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 0
        assert len(p.portal._run_history.pkl) == 0
        assert len(p.portal._run_history.txt) == 0
        assert len(p.portal._run_history.json) == 0