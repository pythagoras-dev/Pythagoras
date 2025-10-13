
from pythagoras import _PortalTester
import pythagoras as pth
from pythagoras._010_basic_portals.basic_portal_core_classes import (
     _get_description_value_by_key)
from pythagoras._040_logging_code_portals.logging_portal_core_classes import (
    LoggingFnCallSignature, LoggingCodePortal
    , _EXCEPTIONS_TODAY_TXT, _EXCESSIVE_LOGGING_TXT
    , _EXCEPTIONS_TOTAL_TXT)


def test_empty_logging_portal(tmpdir):

    with _PortalTester():
        portal = LoggingCodePortal(tmpdir)
        description = portal.describe()
        assert description.shape == (9, 3)

        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TOTAL_TXT) == 0
        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TODAY_TXT) == 0
        assert _get_description_value_by_key(description
                                             , _EXCESSIVE_LOGGING_TXT) == False


def test_exceptions_very_basics(tmpdir):
    # tmpdir = "TEST_EXCEPTIONS_VERY_BASIC_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir):

        @pth.logging(excessive_logging=True)
        def y():
            x = 1 / 0
            print(x)

        try:
            y()
        except:
            pass

        signature = LoggingFnCallSignature(y, {})
        assert len(signature.crashes) == 1
        assert len(signature.execution_outputs) == 1
        assert len(signature.execution_attempts) == 1
        assert len(signature.execution_results) == 0

        assert "ZeroDivisionError" in signature.last_execution_output

    with _PortalTester(LoggingCodePortal, tmpdir) as t:
        description = t.portal.describe()
        assert len(t.portal._crash_history) == 1
        assert len(t.portal._run_history.json) == 2
        assert description.shape == (9, 3)
        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TOTAL_TXT) == 1
        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TODAY_TXT) == 1


def test_exceptions_basics_no_excessive_logging(tmpdir):
    # tmpdir = "TEST_EXCEPTIONS_VERY_BASIC_NO_EXCESSIVE_LOGGING" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir):

        @pth.logging(excessive_logging=False)
        def y():
            x = 1 / 0
            print(x)

        try:
            y()
        except:
            pass

        signature = LoggingFnCallSignature(y, {})
        assert len(signature.crashes) == 0
        assert len(signature.execution_outputs) == 0
        assert len(signature.execution_attempts) == 0
        assert len(signature.execution_results) == 0

    with _PortalTester(LoggingCodePortal, tmpdir) as t:
        description = t.portal.describe()
        assert len(t.portal._crash_history) == 1
        assert len(t.portal._run_history.json) == 0
        assert description.shape == (9, 3)
        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TOTAL_TXT) == 1
        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TODAY_TXT) == 1


def test_exceptions_basics_portal_level_logging(tmpdir):
    # tmpdir = "TEST_EXCEPTIONS_BASIC_PORTAL_LEVEL_LOGGING_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir, excessive_logging=True):

        @pth.logging(excessive_logging=False)
        def y():
            x = 1 / 0
            print(x)

        try:
            y()
        except:
            pass

        signature = LoggingFnCallSignature(y, {})
        assert len(signature.crashes) == 1
        assert len(signature.execution_outputs) == 1
        assert len(signature.execution_attempts) == 1
        assert len(signature.execution_results) == 0

        assert "ZeroDivisionError" in signature.last_execution_output

    with _PortalTester(LoggingCodePortal, tmpdir) as t:
        description = t.portal.describe()
        assert len(t.portal._crash_history) == 1
        assert len(t.portal._run_history.json) == 2
        assert description.shape == (9, 3)
        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TOTAL_TXT) == 1
        assert _get_description_value_by_key(description
                                             , _EXCEPTIONS_TODAY_TXT) == 1