
from pythagoras import ValueAddr, KwArgs
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._320_logging_code_portals import (
    LoggingCodePortal, logging)
from pythagoras._320_logging_code_portals.logging_portal_core_classes import LoggingFnCallSignature
import pythagoras as pth


def plus(x, y):
    print("TEST")
    return x+y


def test_fn_call_signature_attributes(tmpdir):
    # tmpdir = "FN_CALL_SIGNATURE_ATTRIBUTES_" + str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            ):
        new_plus = logging(excessive_logging=True)(plus)
        for i in range(1):
            ValueAddr(new_plus)
            signature = LoggingFnCallSignature(new_plus, KwArgs(x=10, y=-200))
            # assert signature.addr == ValueAddr(signature, portal = p.portal)
            assert ValueAddr(signature) == ValueAddr(signature)
            # assert signature.fn_name == new_plus.name == "plus"
            # assert signature.fn_addr == ValueAddr(new_plus, portal = p.portal)
            # assert signature.packed_kwargs == KwArgs(x=10, y=-200).pack(p.portal)
            # assert signature.fn == new_plus
            # assert signature._kwargs_addr.get() == KwArgs(x=10, y=-200).pack(p.portal)

def test_fn_call_signature_run_history(tmpdir):
    # tmpdir = "FN_CALL_SIGNATURE_RUN_HISTORY_" + str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        new_plus = logging(excessive_logging=True)(plus)
        signature = LoggingFnCallSignature(new_plus, KwArgs(x=-50, y=500))

        N_EXECUTIONS = 4
        for i in range(N_EXECUTIONS):
            assert signature.execute() == 450

        assert len(p.portal._run_history.py) == 1

        assert len(signature.execution_attempts) == N_EXECUTIONS
        assert len(signature.execution_results) == N_EXECUTIONS
        assert len(signature.execution_outputs) == N_EXECUTIONS
        assert len(signature.crashes) == 0
        assert len(signature.events) == 0


def test_fn_call_signature_results_history(tmpdir):
    # tmpdir = "FN_CALL_SIGNATURE_RESULTS_HISTORY_" + str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir):
        x,y = "10","101"
        expected_result = plus(x=x,y=y)
        assert expected_result == "10101"

        new_plus = logging(excessive_logging=True)(plus)
        signature = LoggingFnCallSignature(new_plus, KwArgs(x=x, y=y))

        N_EXECUTIONS = 5
        for i in range(N_EXECUTIONS):
            assert signature.execute() == expected_result

        counter = 0
        for v in signature.execution_results.values():
            counter += 1
            assert v.get() == expected_result
        assert counter == N_EXECUTIONS


def test_fn_call_signature_output_history(tmpdir):
    # tmpdir = "FN_CALL_SIGNATURE_OUTPUT_HISTORY_" + str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir):
        x,y = "10","101"
        expected_result = plus(x=x,y=y)
        assert expected_result == "10101"

        new_plus = logging(excessive_logging=True)(plus)
        signature = LoggingFnCallSignature(new_plus, KwArgs(x=x, y=y))

        N_EXECUTIONS = 10
        for i in range(N_EXECUTIONS):
            signature.execute()

        counter = 0
        for v in signature.execution_outputs.values():
            counter += 1
            assert v.strip() == "TEST"
        assert counter == N_EXECUTIONS


def plus_with_events(x, y):
    pth.log_event(f"TEST {x=}, {y=}")
    pth.log_event("SECOND TEST")
    return x+y


def test_fn_call_signature_events_history(tmpdir):
    # tmpdir = "FN_CALL_SIGNATURE_EVENTS_HISTORY_" + str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        x,y = "10","101"

        new_plus = logging(excessive_logging=True)(plus_with_events)
        signature = LoggingFnCallSignature(new_plus, KwArgs(x=x, y=y))

        N_EXECUTIONS = 8
        for i in range(N_EXECUTIONS):
            signature.execute()

        assert len(signature.events) == N_EXECUTIONS*2
        assert len(p.portal._event_history) == N_EXECUTIONS*2


def test_fn_call_signature_hash_consistency_with_equality(tmpdir):
    """Verify hash/equality contract: equal signatures must have equal hashes."""
    with _PortalTester(LoggingCodePortal, tmpdir):
        fn = logging(excessive_logging=True)(plus)
        sig1 = LoggingFnCallSignature(fn, KwArgs(x=10, y=20))
        sig2 = LoggingFnCallSignature(fn, KwArgs(x=10, y=20))

        assert sig1 == sig2
        assert hash(sig1) == hash(sig2)


def test_fn_call_signature_usable_in_sets(tmpdir):
    """Verify LoggingFnCallSignature instances can be used in sets correctly."""
    with _PortalTester(LoggingCodePortal, tmpdir):
        fn = logging(excessive_logging=True)(plus)
        sig1 = LoggingFnCallSignature(fn, KwArgs(x=10, y=20))
        sig2 = LoggingFnCallSignature(fn, KwArgs(x=10, y=20))
        sig3 = LoggingFnCallSignature(fn, KwArgs(x=99, y=99))

        sig_set = {sig1, sig2, sig3}
        assert len(sig_set) == 2  # sig1 and sig2 are equal


def test_fn_call_signature_usable_as_dict_keys(tmpdir):
    """Verify LoggingFnCallSignature instances can be used as dictionary keys."""
    with _PortalTester(LoggingCodePortal, tmpdir):
        fn = logging(excessive_logging=True)(plus)
        sig1 = LoggingFnCallSignature(fn, KwArgs(x=10, y=20))
        sig2 = LoggingFnCallSignature(fn, KwArgs(x=10, y=20))

        d = {sig1: "value1"}
        d[sig2] = "value2"

        assert len(d) == 1
        assert d[sig1] == "value2"
