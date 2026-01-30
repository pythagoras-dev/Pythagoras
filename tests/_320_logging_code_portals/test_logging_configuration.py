
import pytest
from persidict import KEEP_CURRENT

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._320_logging_code_portals import (
    LoggingCodePortal, logging)


def test_all_defaulta_config(tmpdir):
    # tmpdir = "TOTAL_ALL_DEFAULTS_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            ) as t:
        assert len(t.portal.global_portal_settings) == 0
        assert len(t.portal.local_node_settings) == 0

        @logging()
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        assert len(t.portal.global_portal_settings) == 0
        assert len(t.portal.local_node_settings) == 0

@pytest.mark.parametrize("f",[True,False,KEEP_CURRENT])
@pytest.mark.parametrize("p",[True,False,KEEP_CURRENT])
def test_portal_and_fn_config(tmpdir,f,p):
    # tmpdir = 2*"PORTAL_AND_FN_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            , excessive_logging=p) as t:
        # Portal-level config goes to global_portal_settings
        assert len(t.portal.global_portal_settings) == 1 - int(p==KEEP_CURRENT)
        assert len(t.portal.local_node_settings) == 0

        @logging(excessive_logging=f)
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        # Function-level config goes to local_node_settings
        assert len(t.portal.global_portal_settings) == 1 - int(p==KEEP_CURRENT)
        assert len(t.portal.local_node_settings) == 1 - int(f==KEEP_CURRENT)

        if p==f==KEEP_CURRENT:
            expected_counter = 0
        elif p==KEEP_CURRENT:
            expected_counter = int(f)
        else:
            expected_counter = int(p)

        assert len(t.portal._run_history.py) == expected_counter
        assert len(t.portal._run_history.pkl) == expected_counter
        assert len(t.portal._run_history.txt) == expected_counter


@pytest.mark.parametrize("p",[True,False])
def test_portal_config(tmpdir,p):
    # tmpdir = 3*"PORTAL_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            , excessive_logging=p) as t:
        # Portal-level config goes to global_portal_settings
        assert len(t.portal.global_portal_settings) == 1
        assert len(t.portal.local_node_settings) == 0

        @logging()
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        # No function-level config, so local_node_settings stays empty
        assert len(t.portal.global_portal_settings) == 1
        assert len(t.portal.local_node_settings) == 0
        assert len(t.portal._run_history.py) == int(p)
        assert len(t.portal._run_history.pkl) == int(p)
        assert len(t.portal._run_history.txt) == int(p)


@pytest.mark.parametrize("f",[True,False])
def test_fn_config(tmpdir,f):
    # tmpdir = 5*"FN_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as t:
        assert len(t.portal.local_node_settings) == 0

        @logging(excessive_logging=f)
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        assert len(t.portal.local_node_settings) == 1
        assert len(t.portal._run_history.py) == int(f)
        assert len(t.portal._run_history.pkl) == int(f)
        assert len(t.portal._run_history.txt) == int(f)