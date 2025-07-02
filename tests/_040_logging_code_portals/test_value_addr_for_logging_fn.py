from pythagoras import ValueAddr
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._040_logging_code_portals import (
    LoggingCodePortal, logging)

def wonderful_function():
    print("Hello, world!")

def test_simple_function_value_addr(tmpdir):
    # tmpdir = "SIMPLE_FUNCTION_VALUE_ADDR_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global wonderful_function
        wonderful_function = logging(excessive_logging=True)(wonderful_function)

        addr = ValueAddr(wonderful_function)
        assert len(addr) == 4
        assert "wonderful_function" in addr[2]
        assert "loggingfn" in addr[2]

def plus(x, y):
    return x+y

def test_complex_function_value_addr(tmpdir):
    # tmpdir = "COMPLEX_FUNCTION_VALUE_ADDR_"*2 +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        global plus
        plus = logging(excessive_logging=True)(plus)

        addr = ValueAddr(plus)
        assert len(addr) == 4
        assert "plus" in addr[2]
        assert "loggingfn" in addr[2]
