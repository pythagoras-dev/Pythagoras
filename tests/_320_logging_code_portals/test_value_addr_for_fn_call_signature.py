from pythagoras import ValueAddr, KwArgs
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._320_logging_code_portals import (
    LoggingCodePortal, logging)
from pythagoras._320_logging_code_portals.logging_portal_core_classes import LoggingFnCallSignature


def wonderful_function():
    print("Hello, world!")

def test_simple_signature_value_addr(tmpdir):
    # tmpdir = "SIMPLE_SIGNATURE_VALUE_ADDR_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir):
        global wonderful_function
        wonderful_function = logging(excessive_logging=True)(wonderful_function)
        signature = LoggingFnCallSignature(wonderful_function, KwArgs())

        addr = ValueAddr(signature)
        assert len(addr) == 4
        assert "wonderful_function" in addr[2]
        assert "fncallsignature" in addr[2]

def plus(x, y):
    return x+y

def test_complex_signature_value_addr(tmpdir):
    # tmpdir = "COMPLEX_SIGNATURE_VALUE_ADDR_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir):
        global plus
        plus = logging(excessive_logging=True)(plus)
        signature = LoggingFnCallSignature(plus, KwArgs(x=1, y=2))

        addr = ValueAddr(signature)
        assert len(addr) == 4
        assert "plus" in addr[2]
        assert "fncallsignature" in addr[2]
