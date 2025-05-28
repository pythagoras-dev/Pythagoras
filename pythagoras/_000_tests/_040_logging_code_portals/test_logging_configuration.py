import time

import pytest

from pythagoras import ValueAddr, LoggingFnCallSignature
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._040_logging_code_portals import (
    LoggingCodePortal, logging)


def test_all_defaulta_config(tmpdir):
    # tmpdir = "TOTAL_ALL_DEFAULTS_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            , p_consistency_checks=0) as t:
        assert len(t.portal.config_store) == 0

        @logging()
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        assert len(t.portal.config_store) == 0

@pytest.mark.parametrize("f",[True,False])
@pytest.mark.parametrize("p",[True,False])
def test_portal_and_fn_config(tmpdir,f,p):
    # tmpdir = 2*"PORTAL_AND_FN_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            , excessive_logging=p) as t:
        assert len(t.portal.config_store) == 1

        @logging(excessive_logging=f)
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        assert len(t.portal.config_store) == 2
        assert len(t.portal.run_history.py) == int(f or p)
        assert len(t.portal.run_history.pkl) == int(f or p)
        assert len(t.portal.run_history.txt) == int(f or p)


@pytest.mark.parametrize("p",[True,False])
def test_portal_config(tmpdir,p):
    # tmpdir = 3*"PORTAL_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            , excessive_logging=p) as t:
        assert len(t.portal.config_store) == 1

        @logging()
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        assert len(t.portal.config_store) == 1
        assert len(t.portal.run_history.py) == int(p)
        assert len(t.portal.run_history.pkl) == int(p)
        assert len(t.portal.run_history.txt) == int(p)


@pytest.mark.parametrize("f",[True,False])
def test_fn_config(tmpdir,f):
    # tmpdir = 5*"FN_CONFIG_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as t:
        assert len(t.portal.config_store) == 0

        @logging(excessive_logging=f)
        def simple_function():
            print("Hello, world!")

        assert simple_function() is None

        assert len(t.portal.config_store) == 1
        assert len(t.portal.run_history.py) == int(f)
        assert len(t.portal.run_history.pkl) == int(f)
        assert len(t.portal.run_history.txt) == int(f)
